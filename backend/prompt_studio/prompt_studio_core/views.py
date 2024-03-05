import logging
from typing import Any, Optional

from account.custom_exceptions import DuplicateData
from django.db import IntegrityError
from django.db.models import QuerySet
from django.http import HttpRequest
from permissions.permission import IsOwner
from prompt_studio.processor_loader import ProcessorConfig, load_plugins
from prompt_studio.prompt_studio.exceptions import FilenameMissingError
from prompt_studio.prompt_studio_core.constants import (
    ToolStudioErrors,
    ToolStudioKeys,
    ToolStudioPromptKeys,
)
from prompt_studio.prompt_studio_core.exceptions import (
    IndexingError,
    ToolDeleteError,
)
from prompt_studio.prompt_studio_core.prompt_studio_helper import (
    PromptStudioHelper,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.versioning import URLPathVersioning
from tool_instance.models import ToolInstance
from utils.filtering import FilterHelper
from prompt_studio.prompt_studio_registry.models import PromptStudioRegistry

from .models import CustomTool
from .serializers import CustomToolSerializer, PromptStudioIndexSerializer

logger = logging.getLogger(__name__)


class PromptStudioCoreView(viewsets.ModelViewSet):
    """Viewset to handle all Custom tool related operations."""

    versioning_class = URLPathVersioning

    permission_classes = [IsOwner]
    serializer_class = CustomToolSerializer

    processor_plugins = load_plugins()

    def get_queryset(self) -> Optional[QuerySet]:
        filter_args = FilterHelper.build_filter_args(
            self.request,
            ToolStudioKeys.CREATED_BY,
        )
        if filter_args:
            queryset = CustomTool.objects.filter(
                created_by=self.request.user, **filter_args
            )
        else:
            queryset = CustomTool.objects.filter(
                created_by=self.request.user,
            )
        return queryset

    def create(
        self, request: HttpRequest, *args: tuple[Any], **kwargs: dict[str, Any]
    ) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            raise DuplicateData(
                f"{ToolStudioErrors.TOOL_NAME_EXISTS}, \
                    {ToolStudioErrors.DUPLICATE_API}"
            )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(
        self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]
    ) -> Response:
        instance: CustomTool = self.get_object()
        # Checks if tool is exported
        if hasattr(instance, "prompt_studio_registry"):
            exported_tool_instances_in_use = ToolInstance.objects.filter(
                tool_id__exact=instance.prompt_studio_registry.pk
            )
            dependent_wfs = set()
            for tool_instance in exported_tool_instances_in_use:
                dependent_wfs.add(tool_instance.workflow_id)
            if len(dependent_wfs) > 0:
                logger.info(
                    f"Cannot destroy custom tool {instance.tool_id},"
                    f" depended by workflows {dependent_wfs}"
                )
                raise ToolDeleteError(
                    "Failed to delete tool, its used in other workflows. "
                    "Delete its usages first"
                )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["get"])
    def get_select_choices(self, request: HttpRequest) -> Response:
        """Method to return all static dropdown field values.

        The field values are retrieved from `./static/select_choices.json`.

        Returns:
            Response: Reponse of dropdown dict
        """
        try:
            select_choices: dict[
                str, Any
            ] = PromptStudioHelper.get_select_fields()
            return Response(select_choices, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error occured while fetching select fields {e}")
            return Response(select_choices, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def index_document(self, request: HttpRequest) -> Response:
        """API Entry point method to index input file.

        Args:
            request (HttpRequest)

        Raises:
            IndexingError
            ValidationError

        Returns:
            Response
        """
        serializer = PromptStudioIndexSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tool_id: str = serializer.validated_data.get(
            ToolStudioPromptKeys.TOOL_ID
        )
        file_name: str = serializer.validated_data.get(
            ToolStudioPromptKeys.FILE_NAME
        )
        try:
            unique_id = PromptStudioHelper.index_document(
                tool_id=tool_id,
                file_name=file_name,
                org_id=request.org_id,
                user_id=request.user.user_id,
            )

            for processor_plugin in self.processor_plugins:
                cls = processor_plugin[ProcessorConfig.METADATA][
                    ProcessorConfig.METADATA_SERVICE_CLASS
                ]
                cls.process(
                    tool_id=tool_id,
                    file_name=file_name,
                    org_id=request.org_id,
                    user_id=request.user.user_id,
                )

            if unique_id:
                return Response(
                    {"message": "Document indexed successfully."},
                    status=status.HTTP_200_OK,
                )
            else:
                logger.error(
                    "Error occured while indexing. Unique ID is not valid."
                )
                raise IndexingError()
        except Exception as exc:
            logger.error(f"Error occured while indexing {exc}")
            raise IndexingError()

    @action(detail=True, methods=["post"])
    def fetch_response(self, request: HttpRequest) -> Response:
        """API Entry point method to fetch response to prompt.

        Args:
            request (HttpRequest): _description_

        Raises:
            FilenameMissingError: _description_

        Returns:
            Response
        """
        tool_id: str = request.data.get(ToolStudioPromptKeys.TOOL_ID)
        file_name: str = request.data.get(ToolStudioPromptKeys.FILE_NAME)
        id: str = request.data.get(ToolStudioPromptKeys.ID)

        if not file_name or file_name == ToolStudioPromptKeys.UNDEFINED:
            logger.error("Mandatory field file_name is missing")
            raise FilenameMissingError()
        response: dict[str, Any] = PromptStudioHelper.prompt_responder(
            id=id,
            tool_id=tool_id,
            file_name=file_name,
            org_id=request.org_id,
            user_id=request.user.user_id,
        )
        return Response(response, status=status.HTTP_200_OK)
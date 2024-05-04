import json
import logging
from typing import Optional, Union

from flask import current_app

from core.model_runtime.entities.common_entities import I18nObject
from core.tools.entities.tool_bundle import ApiBasedToolBundle
from core.tools.entities.tool_entities import ApiProviderAuthType, ToolParameter, ToolProviderCredentials
from core.tools.entities.user_entities import UserTool, UserToolProvider
from core.tools.provider.api_tool_provider import ApiBasedToolProviderController
from core.tools.provider.builtin_tool_provider import BuiltinToolProviderController
from core.tools.provider.model_tool_provider import ModelToolProviderController
from core.tools.provider.workflow_tool_provider import WorkflowToolProviderController
from core.tools.tool.tool import Tool
from core.tools.tool.workflow_tool import WorkflowTool
from core.tools.utils.configuration import ToolConfigurationManager
from models.tools import ApiToolProvider, BuiltinToolProvider, WorkflowToolProvider

logger = logging.getLogger(__name__)

class ToolTransformService:
    @staticmethod
    def get_tool_provider_icon_url(provider_type: str, provider_name: str, icon: str) -> Union[str, dict]:
        """
            get tool provider icon url
        """
        url_prefix = (current_app.config.get("CONSOLE_API_URL")
                      + "/console/api/workspaces/current/tool-provider/")
        
        if provider_type == UserToolProvider.ProviderType.BUILTIN.value:
            return url_prefix + 'builtin/' + provider_name + '/icon'
        elif provider_type == UserToolProvider.ProviderType.MODEL.value:
            return url_prefix + 'model/' + provider_name + '/icon'
        elif provider_type in [UserToolProvider.ProviderType.API.value, UserToolProvider.ProviderType.WORKFLOW.value]:
            try:
                return json.loads(icon)
            except:
                return {
                    "background": "#252525",
                    "content": "\ud83d\ude01"
                }
        
        return ''
        
    @staticmethod
    def repack_provider(provider: Union[dict, UserToolProvider]):
        """
            repack provider

            :param provider: the provider dict
        """
        if isinstance(provider, dict) and 'icon' in provider:
            provider['icon'] = ToolTransformService.get_tool_provider_icon_url(
                provider_type=provider['type'],
                provider_name=provider['name'],
                icon=provider['icon']
            )
        elif isinstance(provider, UserToolProvider):
            provider.icon = ToolTransformService.get_tool_provider_icon_url(
                provider_type=provider.type.value,
                provider_name=provider.name,
                icon=provider.icon
            )

    @staticmethod
    def builtin_provider_to_user_provider(
        provider_controller: BuiltinToolProviderController,
        db_provider: Optional[BuiltinToolProvider],
        decrypt_credentials: bool = True
    ) -> UserToolProvider:
        """
        convert provider controller to user provider
        """
        result = UserToolProvider(
            id=provider_controller.identity.name,
            author=provider_controller.identity.author,
            name=provider_controller.identity.name,
            description=I18nObject(
                en_US=provider_controller.identity.description.en_US,
                zh_Hans=provider_controller.identity.description.zh_Hans,
            ),
            icon=provider_controller.identity.icon,
            label=I18nObject(
                en_US=provider_controller.identity.label.en_US,
                zh_Hans=provider_controller.identity.label.zh_Hans,
            ),
            type=UserToolProvider.ProviderType.BUILTIN,
            masked_credentials={},
            is_team_authorization=False,
            tools=[]
        )

        # get credentials schema
        schema = provider_controller.get_credentials_schema()
        for name, value in schema.items():
            result.masked_credentials[name] = \
                ToolProviderCredentials.CredentialsType.default(value.type)

        # check if the provider need credentials
        if not provider_controller.need_credentials:
            result.is_team_authorization = True
            result.allow_delete = False
        elif db_provider:
            result.is_team_authorization = True

            if decrypt_credentials:
                credentials = db_provider.credentials

                # init tool configuration
                tool_configuration = ToolConfigurationManager(
                    tenant_id=db_provider.tenant_id, 
                    provider_controller=provider_controller
                )
                # decrypt the credentials and mask the credentials
                decrypted_credentials = tool_configuration.decrypt_tool_credentials(credentials=credentials)
                masked_credentials = tool_configuration.mask_tool_credentials(credentials=decrypted_credentials)

                result.masked_credentials = masked_credentials
                result.original_credentials = decrypted_credentials

        return result
    
    @staticmethod
    def api_provider_to_controller(
        db_provider: ApiToolProvider,
    ) -> ApiBasedToolProviderController:
        """
        convert provider controller to user provider
        """
        # package tool provider controller
        controller = ApiBasedToolProviderController.from_db(
            db_provider=db_provider,
            auth_type=ApiProviderAuthType.API_KEY if db_provider.credentials['auth_type'] == 'api_key' else 
            ApiProviderAuthType.NONE
        )

        return controller
    
    @staticmethod
    def workflow_provider_to_controller(
        db_provider: WorkflowToolProvider
    ) -> WorkflowToolProviderController:
        """
        convert provider controller to provider
        """
        return WorkflowToolProviderController.from_db(db_provider)
    
    @staticmethod
    def workflow_provider_to_user_provider(
        provider_controller: WorkflowToolProviderController
    ):
        """
        convert provider controller to user provider
        """
        return UserToolProvider(
            id=provider_controller.identity.name,
            author=provider_controller.identity.author,
            name=provider_controller.identity.name,
            description=I18nObject(
                en_US=provider_controller.identity.description.en_US,
                zh_Hans=provider_controller.identity.description.zh_Hans,
            ),
            icon=provider_controller.identity.icon,
            label=I18nObject(
                en_US=provider_controller.identity.label.en_US,
                zh_Hans=provider_controller.identity.label.zh_Hans,
            ),
            type=UserToolProvider.ProviderType.WORKFLOW,
            masked_credentials={},
            is_team_authorization=True,
            tools=[]
        )

    @staticmethod
    def api_provider_to_user_provider(
        provider_controller: ApiBasedToolProviderController,
        db_provider: ApiToolProvider,
        decrypt_credentials: bool = True
    ) -> UserToolProvider:
        """
        convert provider controller to user provider
        """
        username = 'Anonymous'
        try:
            username = db_provider.user.name
        except Exception as e:
            logger.error(f'failed to get user name for api provider {db_provider.id}: {str(e)}')
        # add provider into providers
        credentials = db_provider.credentials
        result = UserToolProvider(
            id=db_provider.id,
            author=username,
            name=db_provider.name,
            description=I18nObject(
                en_US=db_provider.description,
                zh_Hans=db_provider.description,
            ),
            icon=db_provider.icon,
            label=I18nObject(
                en_US=db_provider.name,
                zh_Hans=db_provider.name,
            ),
            type=UserToolProvider.ProviderType.API,
            masked_credentials={},
            is_team_authorization=True,
            tools=[]
        )

        if decrypt_credentials:
            # init tool configuration
            tool_configuration = ToolConfigurationManager(
                tenant_id=db_provider.tenant_id, 
                provider_controller=provider_controller
            )

            # decrypt the credentials and mask the credentials
            decrypted_credentials = tool_configuration.decrypt_tool_credentials(credentials=credentials)
            masked_credentials = tool_configuration.mask_tool_credentials(credentials=decrypted_credentials)

            result.masked_credentials = masked_credentials

        return result
    
    @staticmethod
    def model_provider_to_user_provider(
        db_provider: ModelToolProviderController,
    ) -> UserToolProvider:
        """
        convert provider controller to user provider
        """
        return UserToolProvider(
            id=db_provider.identity.name,
            author=db_provider.identity.author,
            name=db_provider.identity.name,
            description=I18nObject(
                en_US=db_provider.identity.description.en_US,
                zh_Hans=db_provider.identity.description.zh_Hans,
            ),
            icon=db_provider.identity.icon,
            label=I18nObject(
                en_US=db_provider.identity.label.en_US,
                zh_Hans=db_provider.identity.label.zh_Hans,
            ),
            type=UserToolProvider.ProviderType.MODEL,
            masked_credentials={},
            is_team_authorization=db_provider.is_active,
        )
    
    @staticmethod
    def tool_to_user_tool(
        tool: Union[ApiBasedToolBundle, WorkflowTool, Tool], credentials: dict = None, tenant_id: str = None
    ) -> UserTool:
        """
        convert tool to user tool
        """
        if isinstance(tool, Tool):
            # fork tool runtime
            tool = tool.fork_tool_runtime(meta={
                'credentials': credentials,
                'tenant_id': tenant_id,
            })

            # get tool parameters
            parameters = tool.parameters or []
            # get tool runtime parameters
            runtime_parameters = tool.get_runtime_parameters() or []
            # override parameters
            current_parameters = parameters.copy()
            for runtime_parameter in runtime_parameters:
                found = False
                for index, parameter in enumerate(current_parameters):
                    if parameter.name == runtime_parameter.name and parameter.form == runtime_parameter.form:
                        current_parameters[index] = runtime_parameter
                        found = True
                        break

                if not found and runtime_parameter.form == ToolParameter.ToolParameterForm.FORM:
                    current_parameters.append(runtime_parameter)

            user_tool = UserTool(
                author=tool.identity.author,
                name=tool.identity.name,
                label=tool.identity.label,
                description=tool.description.human,
                parameters=current_parameters
            )

            return user_tool
        
        if isinstance(tool, ApiBasedToolBundle):
            return UserTool(
                author=tool.author,
                name=tool.operation_id,
                label=I18nObject(
                    en_US=tool.operation_id,
                    zh_Hans=tool.operation_id
                ),
                description=I18nObject(
                    en_US=tool.summary or '',
                    zh_Hans=tool.summary or ''
                ),
                parameters=tool.parameters
            )
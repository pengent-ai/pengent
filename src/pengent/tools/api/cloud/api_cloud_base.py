from ....lib.singleton import Singleton
from ....lib.custom_logger import get_logger


class CloudResourceBase:
    """
    Base class for cloud resource management.
    """

    def __init__(self, id, status="unknown", metadata: dict = None):
        """
        Initialize the cloud resource API base class.
        :param config: Configuration for the cloud resource API.
        """
        self.id = id
        self.status = status
        self.metadata = metadata if metadata else {}
        self.logger = get_logger()

    def start():
        """
        Start the cloud resource.
        """
        raise NotImplementedError("This method should be overridden in subclasses.")

    def stop():
        """
        Start the cloud resource.
        """
        raise NotImplementedError("This method should be overridden in subclasses.")


class CloudServiceBase(Singleton):
    """
    Base class for cloud service.
    """

    def __init__(self, name: str):
        """
        Initialize the cloud service API base class.
        :param config: Configuration for the cloud service API.
        """
        if hasattr(self, "_initialized") and self._initialized:
            return  # すでに初期化済みなら何もしない
        self.logger = get_logger()
        self.name = name
        self.resources = {}  # 管理しているリソースを格納する
        self.logger.info(f"CloudService initialized with name: {self.name}")
        self._initialized = True

    def get(self):
        """
        サービスのinstance一覧を取得する
        """

    def register_resource(self, resource_id: str, resource_obj: CloudResourceBase):
        """
        Register a resource object to this service.

        Args:
            resource_id (str): ID or name of the resource.
            resource_obj: Resource object instance.
        """
        self.resources[resource_id] = resource_obj
        self.logger.info(f"Registered resource: {resource_id} to service: {self.name}")
        return resource_obj


class CloudPlatformBase(Singleton):
    """
    Base class for cloud platform API interactions.
    """

    def __init__(self, name: str):
        """
        Initialize the cloud platform API base class.
        :param config: Configuration for the cloud platform API.
        """
        if hasattr(self, "_initialized") and self._initialized:
            return  # すでに初期化済みなら何もしない
        self.logger = get_logger()
        self.name = name
        self._services = {}  # サービス一覧を登録できるようにしておく
        self.logger.info(f"CloudPlatfrom : {self.name}")
        self._initialized = True

    def list_services(self) -> list:
        return list(self._services.keys())

    def register_service(self, service_name: str, service_obj: CloudServiceBase):
        """
        Register a service object to the platform.

        Args:
            service_name (str): Name of the service (e.g., "EC2", "S3").
            service_obj: Service object instance.
        """
        self._services[service_name] = service_obj
        self.logger.info(f"Registered service: {service_name}")

    def get_service(self, service_name: str) -> CloudServiceBase:
        """
        Get a service object by its name.

        Args:
            service_name (str): Name of the service (e.g., "EC2", "S3").

        Returns:
            CloudServiceBase: Service object instance.
        """
        return self._services.get(service_name, None)

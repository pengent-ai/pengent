import runpod
import os

from ..api_cloud_base import CloudPlatformBase, CloudServiceBase, CloudResourceBase


class RunpodPodResource(CloudResourceBase):
    """
    Runpod Pod Resource
    """
    def __init__(self, pod_dict: dict):
        super().__init__(
            pod_dict.get("id"), pod_dict.get("desiredStatus", "unknown"), pod_dict
        )

    def show(self):
        return runpod.get_pod(self.id)

    def start(self, gpu_count=1):
        # スポットなら1で渡す必要がある
        return runpod.resume_pod(pod_id=self.id, gpu_count=gpu_count)

    def stop(self):
        return runpod.stop_pod(self.id)

    def delete(self):
        return runpod.terminate_pod(self.id)


class RunpodPodService(CloudServiceBase):
    """
    Runpod Pod Service
    """
    def __init__(self):
        super().__init__(name="pod")

    def get(self):
        pods = runpod.get_pods()
        for pod in pods:
            self.logger.debug(f"Pod ID: {pod['id']}, Status: {pod['desiredStatus']}")
        return pods

    def register_pod(self, pod_dict: dict) -> RunpodPodResource:
        self.logger.debug(f"register_pod: {pod_dict}.")
        pod = RunpodPodResource(pod_dict)
        return super().register_resource(pod_dict["id"], pod)


class ApiRunPod(CloudPlatformBase):
    """
    RunPod API(クラウドサービス)

    Reference:
        - 公式サイト: https://www.runpod.io/
        - ドキュメント: https://docs.runpod.io/sdks/python/overview
    Exampls
        pip install runpod

    Notes:
        - Pods(GPU/CPUインスタンス):
          - オンデマンドまたはスポット価格で利用できるコンテナベースの計算環境
        - Serverless Endpoints:
          - カスタム関数やモデルをAPIエンドポイントとしてデプロイできるサーバレス環境
        - Templates:
          - PodやServerless Endpointの環境設定をテンプレートとして保存・再利用できます。
          - Dockerイメージや環境変数、ストレージ設定などを含めた構成を簡単に管理できます
        - Network Storage:
          - 高速なNVMe SSDを使用したネットワークストレージを提供
          - 複数のPodやEndpoint間でデータを共有できます。
    """

    def __init__(self):
        super().__init__(name="RunPod")
        self.version = runpod.version.get_version()
        runpod.api_key = os.getenv("RUNPOD_API_KEY")
        self.logger.info(f"RunPod API initialized with version: {self.version}")
        self.register_service("pod", RunpodPodService())

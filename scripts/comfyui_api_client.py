"""
comfyui_api_client.py - Cliente Python para la API REST/WebSocket de ComfyUI
ComfyUI Social Media Suite

Permite ejecutar workflows programaticamente y obtener los resultados.
"""
import json
import os
import time
import uuid
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

try:
    import websocket
    from websocket import WebSocketException
except ImportError:
    websocket = None
    WebSocketException = Exception

try:
    import requests
except ImportError:
    requests = None


class ComfyUIClient:
    """Cliente para la API de ComfyUI."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8188,
                 protocol: str = "http"):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.base_url = f"{protocol}://{host}:{port}"
        self.ws_url = f"ws://{host}:{port}/ws"
        self.client_id = str(uuid.uuid4())

    # -----------------------------
    # Health & info
    # -----------------------------

    def is_alive(self, timeout: int = 5) -> bool:
        """Verifica si ComfyUI esta corriendo."""
        try:
            if requests:
                r = requests.get(f"{self.base_url}/system_stats",
                                 timeout=timeout)
                return r.status_code == 200
            else:
                req = urllib.request.Request(f"{self.base_url}/system_stats")
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return resp.status == 200
        except Exception:
            return False

    def get_system_stats(self) -> Dict:
        """Devuelve estadisticas del sistema (GPU, RAM, etc.)."""
        return self._get("/system_stats")

    def get_models(self, folder: str = "checkpoints") -> List[str]:
        """Lista los modelos disponibles en una carpeta."""
        return self._get(f"/object_info/{folder}").get(folder, {}).get("models", [])

    # -----------------------------
    # Workflow execution
    # -----------------------------

    def queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """Encola un workflow y devuelve el prompt_id."""
        payload = {
            "prompt": workflow,
            "client_id": self.client_id
        }
        result = self._post_json("/prompt", payload)
        if "prompt_id" not in result:
            raise RuntimeError(f"ComfyUI no devolvio prompt_id: {result}")
        return result["prompt_id"]

    def get_history(self, prompt_id: str) -> Dict:
        """Obtiene el historial de un prompt."""
        return self._get(f"/history/{prompt_id}").get(prompt_id, {})

    def get_queue(self) -> Dict:
        """Devuelve el estado de la cola."""
        return self._get("/queue")

    def cancel_prompt(self, prompt_id: str) -> Dict:
        """Cancela un prompt en cola."""
        return self._post_json("/cancel", {"cancel": True, "id": prompt_id})

    def interrupt(self) -> Dict:
        """Interrumpe la generacion actual."""
        return self._post_json("/interrupt", {})

    # -----------------------------
    # Wait for completion (WebSocket)
    # -----------------------------

    def wait_for_completion(self, prompt_id: str,
                            timeout: int = 600) -> Dict:
        """
        Espera a que un prompt termine via WebSocket.
        Devuelve el historial del prompt.
        """
        if websocket is None:
            return self._poll_history(prompt_id, timeout)

        ws = websocket.create_connection(
            f"{self.ws_url}?clientId={self.client_id}",
            timeout=timeout
        )
        try:
            while True:
                msg = ws.recv()
                if not msg:
                    continue
                data = json.loads(msg)
                if data.get("type") == "executing":
                    d = data.get("data", {})
                    if d.get("prompt_id") == prompt_id and d.get("node") is None:
                        # Ejecucion completada
                        break
                elif data.get("type") == "execution_error":
                    d = data.get("data", {})
                    if d.get("prompt_id") == prompt_id:
                        raise RuntimeError(
                            f"Error de ejecucion en ComfyUI: {d}"
                        )
                elif data.get("type") == "execution_interrupted":
                    d = data.get("data", {})
                    if d.get("prompt_id") == prompt_id:
                        raise RuntimeError("Ejecucion interrumpida")
        finally:
            ws.close()

        return self.get_history(prompt_id)

    def _poll_history(self, prompt_id: str, timeout: int = 600) -> Dict:
        """Fallback sin WebSocket: poll /history cada 2s."""
        start = time.time()
        while time.time() - start < timeout:
            hist = self.get_history(prompt_id)
            if hist:
                return hist
            time.sleep(2)
        raise TimeoutError(f"Timeout esperando {prompt_id}")

    # -----------------------------
    # Output retrieval
    # -----------------------------

    def get_output_images(self, history: Dict) -> List[Tuple[str, bytes]]:
        """
        Extrae las imagenes de salida del historial.
        Devuelve lista de (filename, bytes).
        """
        images = []
        outputs = history.get("outputs", {})
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                for img in node_output["images"]:
                    fname = img["filename"]
                    subfolder = img.get("subfolder", "")
                    img_type = img.get("type", "output")
                    data = self._get_image(fname, subfolder, img_type)
                    images.append((fname, data))
            elif "gifs" in node_output:
                for g in node_output["gifs"]:
                    fname = g["filename"]
                    subfolder = g.get("subfolder", "")
                    img_type = g.get("type", "output")
                    data = self._get_image(fname, subfolder, img_type)
                    images.append((fname, data))
        return images

    def _get_image(self, filename: str, subfolder: str = "",
                   img_type: str = "output") -> bytes:
        """Descarga una imagen de ComfyUI."""
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": img_type
        }
        if requests:
            r = requests.get(f"{self.base_url}/view", params=params,
                             timeout=60)
            r.raise_for_status()
            return r.content
        else:
            from urllib.parse import urlencode
            url = f"{self.base_url}/view?{urlencode(params)}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()

    # -----------------------------
    # Upload
    # -----------------------------

    def upload_image(self, image_path: str,
                     overwrite: bool = False) -> Dict:
        """Sube una imagen a ComfyUI (carpeta input/)."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(image_path)

        if requests:
            with open(path, "rb") as f:
                files = {"image": (path.name, f)}
                data = {"overwrite": str(overwrite).lower()}
                r = requests.post(f"{self.base_url}/upload/image",
                                  files=files, data=data, timeout=120)
                r.raise_for_status()
                return r.json()
        else:
            # Fallback con urllib (mas limitado)
            raise RuntimeError("upload_image requiere 'requests' instalado")

    # -----------------------------
    # Helpers HTTP
    # -----------------------------

    def _get(self, path: str) -> Dict:
        url = f"{self.base_url}{path}"
        if requests:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            return r.json()
        else:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())

    def _post_json(self, path: str, payload: Dict) -> Dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        if requests:
            r = requests.post(url, data=data,
                              headers={"Content-Type": "application/json"},
                              timeout=30)
            r.raise_for_status()
            return r.json()
        else:
            req = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())


# ============================================================
# Funciones de conveniencia
# ============================================================

def load_workflow_api_json(path: str) -> Dict[str, Any]:
    """
    Carga un workflow exportado en formato API.
    En ComfyUI: Settings -> Enable Dev Mode -> Save (API Format)
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def set_workflow_input(workflow: Dict, node_id: str, input_name: str,
                       value: Any) -> Dict:
    """Modifica un input de un nodo del workflow."""
    if node_id not in workflow:
        raise KeyError(f"Nodo {node_id} no existe en el workflow")
    if "inputs" not in workflow[node_id]:
        workflow[node_id]["inputs"] = {}
    workflow[node_id]["inputs"][input_name] = value
    return workflow


def find_node_by_class(workflow: Dict, class_type: str) -> Optional[str]:
    """Encuentra el ID del primer nodo de una clase dada."""
    for node_id, node in workflow.items():
        if node.get("class_type") == class_type:
            return node_id
    return None


def find_nodes_by_class(workflow: Dict, class_type: str) -> List[str]:
    """Encuentra todos los IDs de nodos de una clase dada."""
    return [nid for nid, n in workflow.items()
            if n.get("class_type") == class_type]


# ============================================================
# Ejemplo de uso
# ============================================================

if __name__ == "__main__":
    client = ComfyUIClient()

    print(f"ComfyUI vivo: {client.is_alive()}")
    if client.is_alive():
        stats = client.get_system_stats()
        print(f"Sistema: {json.dumps(stats, indent=2)[:500]}")

        print(f"\nCheckpoints disponibles:")
        for cp in client.get_models("checkpoints"):
            print(f"  - {cp}")

        # Ejemplo: ejecutar un workflow
        # wf = load_workflow_api_json("workflows/instagram_post_api.json")
        # wf = set_workflow_input(wf, "6", "text", "mi prompt aqui")
        # prompt_id = client.queue_prompt(wf)
        # print(f"Encolado: {prompt_id}")
        # history = client.wait_for_completion(prompt_id)
        # images = client.get_output_images(history)
        # for fname, data in images:
        #     with open(f"output_{fname}", "wb") as f:
        #         f.write(data)
        #     print(f"Imagen guardada: output_{fname}")

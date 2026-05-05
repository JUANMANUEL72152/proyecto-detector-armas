import React, { useState, useRef, useEffect, useCallback } from "react";

const BACKEND_URL = "http://127.0.0.1:5000"; // Puerto unificado Flask
const DETECTION_INTERVAL_MS = 1000;          // Detectar cada 1 segundo

export default function WeaponDetectionWebUI() {
  const [isRunning, setIsRunning] = useState(false);
  const [detections, setDetections] = useState([]);
  const [error, setError] = useState(null);
  const [isDetecting, setIsDetecting] = useState(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);

  // ── Iniciar cámara ──────────────────────────────────────────
  const startCamera = async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      videoRef.current.srcObject = stream;
      setIsRunning(true);
    } catch (err) {
      setError("No se pudo acceder a la cámara. Verifica los permisos del navegador.");
    }
  };

  // ── Detener cámara ──────────────────────────────────────────
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsRunning(false);
    setDetections([]);
    setIsDetecting(false);
    // Limpiar canvas
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  };

  // ── Capturar frame y enviarlo al backend ────────────────────
  const detectFrame = useCallback(async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return;

    // Capturar frame del video al canvas
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);

    // Convertir canvas a blob y enviarlo al backend
    canvas.toBlob(async (blob) => {
      if (!blob) return;
      setIsDetecting(true);

      const formData = new FormData();
      formData.append("file", new File([blob], "frame.jpg", { type: "image/jpeg" }));

      try {
        const res = await fetch(`${BACKEND_URL}/api/detect`, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.error || `Error HTTP ${res.status}`);
        }

        const data = await res.json();
        setDetections(data.detections || []);
        setError(null);
        drawDetections(ctx, data.detections || [], canvas.width, canvas.height);
      } catch (err) {
        setError(`Error al detectar: ${err.message}`);
      } finally {
        setIsDetecting(false);
      }
    }, "image/jpeg", 0.8);
  }, []);

  // ── Dibujar bounding boxes sobre el canvas ──────────────────
  const drawDetections = (ctx, detections, width, height) => {
    // Redibujar el frame actual antes de los boxes
    const video = videoRef.current;
    if (video) ctx.drawImage(video, 0, 0, width, height);

    ctx.lineWidth = 3;
    ctx.font = "bold 16px Arial";

    detections.forEach((det) => {
      const [x, y, w, h] = det.box;
      const isDangerous = ["gun", "knife", "arma", "pistola", "cuchillo"].includes(
        det.label.toLowerCase()
      );
      const color = isDangerous ? "#ff3333" : "#33ff33";

      // Caja
      ctx.strokeStyle = color;
      ctx.strokeRect(x, y, w, h);

      // Fondo de la etiqueta
      const label = `${det.label} ${(det.confidence * 100).toFixed(1)}%`;
      const textWidth = ctx.measureText(label).width;
      ctx.fillStyle = color;
      ctx.fillRect(x, y > 20 ? y - 22 : y, textWidth + 8, 22);

      // Texto de la etiqueta
      ctx.fillStyle = "#000000";
      ctx.fillText(label, x + 4, y > 20 ? y - 5 : y + 16);
    });
  };

  // ── Iniciar/detener el intervalo de detección cuando cambia isRunning ──
  useEffect(() => {
    if (isRunning) {
      intervalRef.current = setInterval(detectFrame, DETECTION_INTERVAL_MS);
    } else {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    return () => clearInterval(intervalRef.current);
  }, [isRunning, detectFrame]);

  // ── Cleanup al desmontar el componente ──────────────────────
  useEffect(() => {
    return () => stopCamera();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center p-6">
      <h1 className="text-3xl font-bold mb-2">🎯 Detector de Armas - YOLOv8</h1>
      <p className="text-gray-400 mb-6 text-sm">Detección automática en tiempo real</p>

      {/* Error */}
      {error && (
        <div className="bg-red-800 border border-red-500 text-red-100 px-4 py-3 rounded mb-4 w-full max-w-2xl">
          ⚠️ {error}
        </div>
      )}

      {/* Video + Canvas superpuesto */}
      <div className="relative mb-4">
        <video
          ref={videoRef}
          autoPlay
          muted
          className="rounded-lg border-4 border-gray-600 w-[640px] h-[480px] bg-black"
        />
        <canvas
          ref={canvasRef}
          className="absolute top-0 left-0 rounded-lg w-[640px] h-[480px]"
        />
        {/* Indicador de detección activa */}
        {isRunning && (
          <div className="absolute top-3 right-3 flex items-center gap-2 bg-black bg-opacity-60 px-3 py-1 rounded-full text-sm">
            <span className={`w-2 h-2 rounded-full ${isDetecting ? "bg-yellow-400 animate-pulse" : "bg-green-400"}`} />
            {isDetecting ? "Detectando..." : "En vivo"}
          </div>
        )}
      </div>

      {/* Controles */}
      <div className="flex gap-3 mb-6">
        {!isRunning ? (
          <button
            onClick={startCamera}
            className="bg-green-600 hover:bg-green-700 px-6 py-2 rounded-lg font-semibold transition"
          >
            ▶ Iniciar Cámara
          </button>
        ) : (
          <button
            onClick={stopCamera}
            className="bg-red-600 hover:bg-red-700 px-6 py-2 rounded-lg font-semibold transition"
          >
            ⏹ Detener
          </button>
        )}
      </div>

      {/* Lista de detecciones */}
      <div className="w-full max-w-2xl bg-gray-800 rounded-lg p-4">
        <h2 className="text-lg font-semibold mb-3">
          📋 Detecciones{" "}
          {detections.length > 0 && (
            <span className="text-sm bg-red-600 px-2 py-0.5 rounded-full ml-2">
              {detections.length}
            </span>
          )}
        </h2>
        {detections.length === 0 ? (
          <p className="text-gray-500 text-sm">
            {isRunning ? "Apunta la cámara a un objeto para detectar." : "Inicia la cámara para comenzar."}
          </p>
        ) : (
          <ul className="space-y-2">
            {detections.map((d, i) => {
              const isDangerous = ["gun", "knife", "arma", "pistola", "cuchillo"].includes(
                d.label.toLowerCase()
              );
              return (
                <li
                  key={i}
                  className={`flex justify-between items-center px-3 py-2 rounded ${
                    isDangerous ? "bg-red-900 border border-red-600" : "bg-gray-700"
                  }`}
                >
                  <span className="font-medium">
                    {isDangerous ? "⚠️" : "✅"} {d.label.toUpperCase()}
                  </span>
                  <span className="text-sm text-gray-300">
                    {(d.confidence * 100).toFixed(1)}% confianza
                  </span>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}


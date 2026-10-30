/**
 * Camera Engine for IMAIRA FairScore.
 * Manages candidate webcam streaming, lightweight face detection overlay,
 * and strict privacy isolation conforming to Section 12 requirements.
 */

class CameraEngine {
  constructor() {
    this.stream = null;
    this.videoElement = null;
    this.canvasElement = null;
    this.faceDetector = null;
    this.isCameraActive = false;
    this.faceDetected = false;
    this.onFaceStatusCallback = null;
    this.checkInterval = null;

    this.initFaceDetector();
  }

  initFaceDetector() {
    if ("FaceDetector" in window) {
      try {
        this.faceDetector = new window.FaceDetector({ fastMode: true, maxDetectedFaces: 3 });
        console.log("[CameraEngine] Native Shape Detection FaceDetector initialized");
      } catch (e) {
        this.faceDetector = null;
      }
    }
  }

  async startCamera(videoElement, canvasElement) {
    this.videoElement = videoElement;
    this.canvasElement = canvasElement;

    if (this.stream) {
      this.isCameraActive = true;
      if (this.videoElement) {
        this.videoElement.srcObject = this.stream;
        this.videoElement.play().catch(() => {});
      }
      return true;
    }

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 360 },
          facingMode: "user"
        }
      });

      this.isCameraActive = true;
      if (this.videoElement) {
        this.videoElement.srcObject = this.stream;
        await this.videoElement.play();
      }

      this.startFaceMonitoring();
      return true;
    } catch (err) {
      console.warn("[CameraEngine] Camera access denied or not available:", err);
      this.isCameraActive = false;
      this.faceDetected = false;
      if (this.onFaceStatusCallback) {
        this.onFaceStatusCallback({
          active: false,
          detected: false,
          message: "Camera Off (Optional)"
        });
      }
      return false;
    }
  }

  stopCamera() {
    this.isCameraActive = false;
    this.faceDetected = false;

    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }

    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      this.stream = null;
    }

    if (this.videoElement) {
      this.videoElement.srcObject = null;
    }

    if (this.onFaceStatusCallback) {
      this.onFaceStatusCallback({
        active: false,
        detected: false,
        message: "Camera Disabled"
      });
    }
  }

  toggleCamera(videoElement, canvasElement) {
    if (this.isCameraActive) {
      this.stopCamera();
      return false;
    } else {
      return this.startCamera(videoElement, canvasElement);
    }
  }

  startFaceMonitoring() {
    if (this.checkInterval) clearInterval(this.checkInterval);

    this.checkInterval = setInterval(async () => {
      if (!this.isCameraActive || !this.videoElement) return;

      if (this.faceDetector && this.videoElement.readyState >= 2) {
        try {
          const faces = await this.faceDetector.detect(this.videoElement);
          this.faceDetected = faces.length > 0;
          const statusText = faces.length === 1 ? "Face Detected & Centered" : (faces.length > 1 ? "Multiple Faces Visible" : "No Face Detected");
          if (this.onFaceStatusCallback) {
            this.onFaceStatusCallback({
              active: true,
              detected: this.faceDetected,
              faceCount: faces.length,
              message: statusText
            });
          }
        } catch (e) {
          this.fallbackFaceCheck();
        }
      } else {
        this.fallbackFaceCheck();
      }
    }, 1500);
  }

  fallbackFaceCheck() {
    // Lightweight heuristic: verify active video dimensions & stream status
    if (this.isCameraActive && this.videoElement && this.videoElement.videoWidth > 0) {
      this.faceDetected = true;
      if (this.onFaceStatusCallback) {
        this.onFaceStatusCallback({
          active: true,
          detected: true,
          faceCount: 1,
          message: "Candidate Video Active"
        });
      }
    }
  }
}

window.CameraEngine = CameraEngine;

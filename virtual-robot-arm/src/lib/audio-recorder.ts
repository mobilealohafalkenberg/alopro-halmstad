/**
 * Audio recorder that captures microphone input and resamples to 16kHz PCM16
 * for Gemini Live API compatibility
 */

export class AudioRecorder {
  private audioContext: AudioContext | null = null;
  private mediaStream: MediaStream | null = null;
  private workletNode: AudioWorkletNode | null = null;
  private isRecording = false;

  constructor(
    private onAudioData: (base64Data: string) => void,
    private onError?: (error: Error) => void
  ) {}

  async start() {
    if (this.isRecording) {
      console.warn('Already recording');
      return;
    }

    try {
      // Get microphone access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // Create audio context with default sample rate
      this.audioContext = new AudioContext();
      const source = this.audioContext.createMediaStreamSource(this.mediaStream);

      // Load and create audio worklet for processing
      await this.audioContext.audioWorklet.addModule(
        URL.createObjectURL(
          new Blob([this.getWorkletCode()], { type: 'application/javascript' })
        )
      );

      this.workletNode = new AudioWorkletNode(this.audioContext, 'audio-processor');

      // Listen for processed audio data
      this.workletNode.port.onmessage = (event) => {
        if (event.data.type === 'audio') {
          const pcm16Base64 = this.arrayBufferToBase64(event.data.buffer);
          this.onAudioData(pcm16Base64);
        }
      };

      // Connect nodes
      source.connect(this.workletNode);
      this.workletNode.connect(this.audioContext.destination);

      this.isRecording = true;
      console.log('Audio recording started');
    } catch (error) {
      const err = error as Error;
      console.error('Failed to start audio recording:', err);
      this.onError?.(err);
      throw err;
    }
  }

  async stop() {
    if (!this.isRecording) {
      return;
    }

    // Disconnect and cleanup
    this.workletNode?.disconnect();
    this.workletNode = null;

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }

    if (this.audioContext) {
      await this.audioContext.close();
      this.audioContext = null;
    }

    this.isRecording = false;
    console.log('Audio recording stopped');
  }

  getIsRecording(): boolean {
    return this.isRecording;
  }

  /**
   * Audio worklet processor code that resamples to 16kHz and converts to PCM16
   */
  private getWorkletCode(): string {
    return `
      class AudioProcessor extends AudioWorkletProcessor {
        constructor() {
          super();
          this.targetSampleRate = 16000;
          this.sourceSampleRate = sampleRate;
          this.buffer = [];
          this.resampleRatio = this.sourceSampleRate / this.targetSampleRate;
          this.resampleIndex = 0;
        }

        process(inputs, outputs, parameters) {
          const input = inputs[0];
          if (!input || !input[0]) {
            return true;
          }

          const inputData = input[0]; // First channel

          // Resample to 16kHz
          for (let i = 0; i < inputData.length; i++) {
            this.resampleIndex += 1;

            if (this.resampleIndex >= this.resampleRatio) {
              this.resampleIndex -= this.resampleRatio;
              this.buffer.push(inputData[i]);
            }
          }

          // Send chunks of ~100ms (1600 samples at 16kHz)
          const chunkSize = 1600;
          if (this.buffer.length >= chunkSize) {
            const chunk = this.buffer.splice(0, chunkSize);

            // Convert Float32 to PCM16
            const pcm16 = new Int16Array(chunk.length);
            for (let i = 0; i < chunk.length; i++) {
              const s = Math.max(-1, Math.min(1, chunk[i]));
              pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            }

            this.port.postMessage({
              type: 'audio',
              buffer: pcm16.buffer
            }, [pcm16.buffer]);
          }

          return true;
        }
      }

      registerProcessor('audio-processor', AudioProcessor);
    `;
  }

  /**
   * Convert ArrayBuffer to base64 string
   */
  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }
}

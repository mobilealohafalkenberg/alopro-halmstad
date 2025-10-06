/**
 * Copyright 2024 Google LLC
 *
 * Adapted for Virtual Robot Arm Simulator
 */

import {
  Content,
  GoogleGenAI,
  LiveCallbacks,
  LiveClientToolResponse,
  LiveConnectConfig,
  LiveServerContent,
  LiveServerMessage,
  LiveServerToolCall,
  LiveServerToolCallCancellation,
  Part,
  Session,
} from "@google/genai";

import { EventEmitter } from "eventemitter3";

export interface LiveClientEventTypes {
  audio: (data: ArrayBuffer) => void;
  close: (event: CloseEvent) => void;
  content: (data: LiveServerContent) => void;
  error: (error: ErrorEvent) => void;
  interrupted: () => void;
  open: () => void;
  setupcomplete: () => void;
  toolcall: (toolCall: LiveServerToolCall) => void;
  toolcallcancellation: (toolcallCancellation: LiveServerToolCallCancellation) => void;
  turncomplete: () => void;
}

export interface LiveClientOptions {
  apiKey: string;
}

export class GenAILiveClient extends EventEmitter<LiveClientEventTypes> {
  protected client: GoogleGenAI;
  private _status: "connected" | "disconnected" | "connecting" = "disconnected";
  private _session: Session | null = null;
  private _model: string | null = null;
  protected config: LiveConnectConfig | null = null;

  public get status() {
    return this._status;
  }

  public get session() {
    return this._session;
  }

  public get model() {
    return this._model;
  }

  public getConfig() {
    return { ...this.config };
  }

  constructor(options: LiveClientOptions) {
    super();
    this.client = new GoogleGenAI(options);
  }

  async connect(model: string, config: LiveConnectConfig): Promise<boolean> {
    if (this._status === "connected" || this._status === "connecting") {
      return false;
    }

    this._status = "connecting";
    this.config = config;
    this._model = model;

    const callbacks: LiveCallbacks = {
      onopen: () => {
        console.log('Connected to Gemini Live API');
        this.emit("open");
      },
      onmessage: (message: LiveServerMessage) => this.handleMessage(message),
      onerror: (e: ErrorEvent) => {
        console.error('Gemini Live API error:', e);
        this.emit("error", e);
      },
      onclose: (e: CloseEvent) => {
        console.log('Disconnected from Gemini Live API');
        this.emit("close", e);
      },
    };

    try {
      this._session = await this.client.live.connect({
        model,
        config,
        callbacks,
      });
      this._status = "connected";
      return true;
    } catch (e) {
      console.error("Error connecting to GenAI Live:", e);
      this._status = "disconnected";
      return false;
    }
  }

  public disconnect() {
    if (!this.session) {
      return false;
    }
    this.session?.close();
    this._session = null;
    this._status = "disconnected";
    return true;
  }

  protected handleMessage(message: LiveServerMessage) {
    if (message.setupComplete) {
      console.log('Setup complete');
      this.emit("setupcomplete");
      return;
    }

    if (message.toolCall) {
      console.log('Tool call received:', message.toolCall);
      this.emit("toolcall", message.toolCall);
      return;
    }

    if (message.toolCallCancellation) {
      this.emit("toolcallcancellation", message.toolCallCancellation);
      return;
    }

    if (message.serverContent) {
      const { serverContent } = message;

      if ("interrupted" in serverContent) {
        this.emit("interrupted");
        return;
      }

      if ("turnComplete" in serverContent) {
        this.emit("turncomplete");
      }

      if ("modelTurn" in serverContent) {
        const parts: Part[] = serverContent.modelTurn?.parts || [];

        // Handle audio parts
        const audioParts = parts.filter(
          (p) => p.inlineData && p.inlineData.mimeType?.startsWith("audio/pcm")
        );

        audioParts.forEach((part) => {
          if (part.inlineData?.data) {
            const data = base64ToArrayBuffer(part.inlineData.data);
            this.emit("audio", data);
          }
        });

        // Handle text/other parts
        const otherParts = parts.filter(
          (p) => !p.inlineData || !p.inlineData.mimeType?.startsWith("audio/pcm")
        );

        if (otherParts.length) {
          const content: { modelTurn: Content } = { modelTurn: { parts: otherParts } };
          this.emit("content", content);
        }
      }
    }
  }

  sendRealtimeInput(chunks: Array<{ mimeType: string; data: string }>) {
    chunks.forEach(chunk => {
      this.session?.sendRealtimeInput({ media: chunk });
    });
  }

  sendToolResponse(toolResponse: LiveClientToolResponse) {
    if (toolResponse.functionResponses && toolResponse.functionResponses.length) {
      this.session?.sendToolResponse({
        functionResponses: toolResponse.functionResponses,
      });
    }
  }

  send(parts: Part | Part[], turnComplete: boolean = true) {
    this.session?.sendClientContent({
      turns: Array.isArray(parts) ? parts : [parts],
      turnComplete
    });
  }
}

function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binaryString = atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}

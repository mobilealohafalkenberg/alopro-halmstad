import { GoogleGenAI } from "@google/genai";
import { config } from "dotenv";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load .env from virtual-robot-arm directory
config({ path: join(__dirname, "virtual-robot-arm", ".env") });

const ai = new GoogleGenAI({
  apiKey: process.env.REACT_APP_GEMINI_API_KEY
});

async function main() {
  try {
    const apiKey = process.env.REACT_APP_GEMINI_API_KEY;
    console.log("Testing Gemini API connection...");
    console.log("API Key length:", apiKey?.length);
    console.log("API Key first 10 chars:", apiKey?.substring(0, 10));
    console.log("API Key last 5 chars:", apiKey?.substring(apiKey.length - 5));

    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: "Say 'API key works!' if you can read this.",
    });

    console.log("\n✓ Success! Response:");
    console.log(response.text);
  } catch (error) {
    console.error("\n✗ Error:", error.message);
    process.exit(1);
  }
}

await main();

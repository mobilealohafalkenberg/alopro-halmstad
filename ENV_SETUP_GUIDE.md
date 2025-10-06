# Environment Setup Guide - API Key Configuration

This guide helps you set up the `.env` files across all project directories.

## Overview

I've created `.env.example` files in 4 locations. You need to:
1. Copy each `.env.example` to `.env`
2. Replace `your-gemini-api-key-here` with your actual API key

## Get Your Gemini API Key

1. Go to [https://aistudio.google.com](https://aistudio.google.com)
2. Sign in with your Google account
3. Click "Get API Key"
4. Copy your API key

## Setup Instructions

### 1. Python Scripts

```bash
cd python_scripts
cp .env.example .env
nano .env  # or use your preferred editor
```

**Variables:**
- `GEMINI_API_KEY` - Your Gemini API key

**Used by:** google-genai Python library

---

### 2. Gemini Live API Control (Python Bridge)

```bash
cd gemini-live/gemini-live-api-control
cp .env.example .env
nano .env
```

**Variables:**
- `GEMINI_API_KEY` - Your Gemini API key

**Used by:**
- Python bridge scripts (`bridges/`)
- Research examples (`research/`)

---

### 3. Live API Console (Robot Control UI)

```bash
cd gemini-live/gemini-live-api-control/live-api-console
cp .env.example .env
nano .env
```

**Variables:**
- `REACT_APP_GEMINI_API_KEY` - Your Gemini API key (REQUIRED)
- `REACT_APP_ROBOT_ENDPOINT` - Robot bridge URL (optional, default: http://localhost:8081)

**Used by:** React frontend for voice-controlled robot

**⚠️ Important:** Must restart dev server after changing `.env`

---

### 4. Live API Web Console (Demo/Starter)

```bash
cd live-api-web-console
cp .env.example .env
nano .env
```

**Variables:**
- `REACT_APP_GEMINI_API_KEY` - Your Gemini API key

**Used by:** Basic Gemini Live API demo console

**⚠️ Important:** Must restart dev server after changing `.env`

---

## Quick Setup Script

Run this from the project root to copy all `.env.example` files:

```bash
# Copy all .env.example files to .env
cp python_scripts/.env.example python_scripts/.env
cp gemini-live/gemini-live-api-control/.env.example gemini-live/gemini-live-api-control/.env
cp gemini-live/gemini-live-api-control/live-api-console/.env.example gemini-live/gemini-live-api-control/live-api-console/.env
cp live-api-web-console/.env.example live-api-web-console/.env

echo "✓ All .env files created!"
echo "Now edit each .env file and add your Gemini API key"
```

Then edit each `.env` file and replace `your-gemini-api-key-here` with your actual API key.

---

## Verification

### Check Python Scripts
```bash
cd python_scripts
grep GEMINI_API_KEY .env
# Should show: GEMINI_API_KEY=AIza...
```

### Check React Apps
```bash
cd gemini-live/gemini-live-api-control/live-api-console
grep REACT_APP_GEMINI_API_KEY .env
# Should show: REACT_APP_GEMINI_API_KEY=AIza...
```

---

## Troubleshooting

### "REACT_APP_GEMINI_API_KEY is not defined"
- Make sure the `.env` file exists in the correct directory
- Restart the dev server (`npm start`)
- Verify the variable starts with `REACT_APP_` prefix

### "No API key found" (Python)
- Check the `.env` file exists
- Verify the key name is `GEMINI_API_KEY`
- No quotes needed around the value

### API Key Security

**✅ Safe (files in .gitignore):**
- `.env` files are ignored by git
- Never committed to repository

**⚠️ Don't:**
- Commit `.env` files
- Share your API keys
- Use production keys in development

---

## Summary

**4 directories need `.env` files:**

| Directory | File | Variables |
|-----------|------|-----------|
| `python_scripts/` | `.env` | `GEMINI_API_KEY` |
| `gemini-live/gemini-live-api-control/` | `.env` | `GEMINI_API_KEY` |
| `gemini-live/.../live-api-console/` | `.env` | `REACT_APP_GEMINI_API_KEY`, `REACT_APP_ROBOT_ENDPOINT` |
| `live-api-web-console/` | `.env` | `REACT_APP_GEMINI_API_KEY` |

**All use the same Gemini API key** - just copy your key to each file.

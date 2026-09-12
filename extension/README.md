# Continuo Chrome Extension — Manifest V3

> AI Context Continuity Companion for Chrome, Brave, and Edge.

## Overview
The Continuo Companion is a Manifest V3 browser extension that captures conversation context from AI interfaces (ChatGPT, Claude, Gemini) and synchronizes it directly into your Continuo Project Memory.

## Features
- **1-Click DOM Parsing**: Extracts decisions, constraints, requirements, and current working states directly from active chat nodes.
- **Provider-Neutral Context**: Works across ChatGPT, Claude, and Gemini without modifying native workflows.
- **Quality Score Telemetry**: Real-time completeness and consistency validation before transit.
- **Quick Cross-AI Handoff**: Generates model-optimized prompt handoffs (e.g. Claude XML spec) and opens target assistants with 1 click.
- **Privacy-First Architecture**: Minimal tab permissions; conversations are never stored for third-party AI training.

## How to Install in Chrome / Brave / Edge

1. Open `chrome://extensions/` in your browser.
2. Toggle **Developer mode** in the upper-right corner.
3. Click **Load unpacked**.
4. Select the `extension/` directory inside this repository (`C:\Users\HP\.gemini\antigravity-ide\scratch\continuo\extension`).
5. The Continuo logo will appear in your browser toolbar!

## How to Use
1. Open a technical discussion in [ChatGPT](https://chatgpt.com/) or [Claude](https://claude.ai/).
2. Click the Continuo toolbar icon.
3. Select your target project.
4. Click **Capture Conversation Context**.
5. Continuo will synthesize a structured Context Package, update the project version, and prepare your handoff payload!

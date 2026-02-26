# Chatbot Project

This repository contains two versions of a voice-guided robotics chatbot system:

- `final-project/`: latest version (recommended)
- `chatbot-project/`: earlier prototype

The system uses OpenAI models to:

- interpret a camera image,
- infer the next task/action,
- generate or reuse robot action codes,
- and guide execution through a controller loop.

## Repository Layout

- `final-project/main.py`: entry point for the final version
- `final-project/model/controller.py`: main orchestration loop (chatbot, model, MCU command flow)
- `final-project/chatbot/chatbot.py`: OpenAI API integration (image + ReAct/action generation)
- `final-project/model/model.py`: local task memory in JSON (`task_blocks.json`)
- `final-project/graph/graph_manager.py`: Neo4j integration for task/action graph data
- `final-project/data/`: prompts, sample image, and task memory file

Legacy prototype:

- `chatbot-project/main.py`
- `chatbot-project/model/controller.py`

## Main Features (final-project)

- Image-based object/task context extraction (`process_image`)
- ReAct-style next-action generation (`generate_action`)
- Local task memory and dependency tracking in JSON
- Optional Neo4j task/action graph persistence
- MCU command dispatch abstraction (`send_command_to_mcu`)

## Requirements

Python 3.10+ recommended.

Install packages (minimum for final-project):

```bash
pip install openai neo4j rich pyserial SpeechRecognition pyttsx3 python-dotenv
```

If you also want the older camera/computer-vision dependencies used in the prototype:

```bash
pip install numpy opencv-python pyrealsense2 ultralytics
```

## Environment Setup (.env)

1. Create your local environment file from the template:

```bash
cp .env.example .env
```

2. Edit `.env` and set your real values:

- `OPENAI_API_KEY` (required)
- `OPENAI_MODEL` (optional, default: `gpt-4o`)
- `NEO4J_URI` (optional, default: `bolt://localhost:7687`)
- `NEO4J_USER` (optional, default: `neo4j`)
- `NEO4J_PASSWORD` (required for `final-project`)

`.env` is ignored by git via `.gitignore`.

## Quick Start (final-project)

1. Move into the final project directory:

```bash
cd final-project
```

2. Ensure `.env` is configured in repo root or in `final-project/`.

3. Run:

```bash
python main.py
```

## Configuration Notes

- Prompts are stored in `final-project/data/`:
  - `gpt_prompt.txt`
  - `image_prompt.txt`
  - `pause_prompt.txt`
  - `react_prompt.txt`
- Task memory is saved in `final-project/data/task_blocks.json`.
- Current code uses `data/test_image.jpg` as the input image source in the controller stub.

## Runtime Flow (final-project)

1. Load prompts and initialize `Controller`
2. Activate chatbot
3. Process an image and extract object/task context
4. Generate next task and action code from history + dependencies
5. Send command to MCU layer
6. Standardize observation and store updated task block/dependency
7. Repeat until model returns `task_name == "None"`

## Known Limitations

- Serial communication and voice I/O are partially stubbed or commented.
- Vision capture is currently mocked to a local test image path.
- Dependency installation is not yet pinned by a dedicated requirements file in `final-project`.

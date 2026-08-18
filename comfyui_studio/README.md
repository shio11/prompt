# ComfyUI Studio

ComfyUIをレンダリングエンジンとして利用し、以下をシンプルなWeb UIから使えるようにするアプリケーションです。

- テキスト→画像生成
- 画像→動画生成（Stable Video Diffusion）
- アップスケール（Real-ESRGAN系モデル）
- フレーム補間（RIFE）
- Qwen3.8によるプロンプト相談エージェント（「こんな画像を作りたいんだけど」に応答してプロンプトを提案）

中身はComfyUIのHTTP APIを呼び出しているだけで、ノードグラフの複雑さをユーザーから隠した簡易フロントエンドです。

## 必要な環境

1. **ComfyUI本体**（別途起動しておくこと）
   - `http://127.0.0.1:8188` で起動している想定（`COMFYUI_BASE_URL` で変更可）
   - 画像生成: 標準ノードのみで動作
   - 動画生成: `ImageOnlyCheckpointLoader` / `SVD_img2vid_Conditioning` などSVD系の標準ノードを使用（Stable Video Diffusionのcheckpointが必要）
   - アップスケール: 標準ノード（`UpscaleModelLoader` / `ImageUpscaleWithModel`）＋ Real-ESRGAN系モデルファイル
   - フレーム補間: カスタムノード **[ComfyUI-Frame-Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation)**（`RIFE VFI`）と **[ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)**（`VHS_LoadVideo` / `VHS_VideoCombine`）が必要
2. **Ollama**（Qwen3.8エージェント用、`http://127.0.0.1:11434` 想定）
   - `ollama pull qwen3:8b` などでモデルを取得しておく

## セットアップ

```bash
cd comfyui_studio/src
pip install -r requirements.txt
python main.py
```

起動後 `http://localhost:8000` でUIが開きます。

## 環境変数

| 変数名 | 説明 | デフォルト |
| --- | --- | --- |
| `COMFYUI_BASE_URL` | ComfyUIサーバーのURL | `http://127.0.0.1:8188` |
| `OLLAMA_BASE_URL` | OllamaサーバーのURL | `http://127.0.0.1:11434` |
| `QWEN_MODEL_NAME` | Ollama上のQwenモデル名 | `qwen3:8b` |
| `DB_PATH` | ジョブ履歴DB(SQLite)のパス | `src/data/jobs.db` |
| `WORKFLOWS_DIR` | ワークフローテンプレートのディレクトリ | `src/workflows` |
| `OUTPUT_DIR` | 生成物の保存先 | `src/data/outputs` |
| `COMFYUI_POLL_INTERVAL_SEC` | ComfyUI完了待ちのポーリング間隔(秒) | `1.0` |
| `COMFYUI_TIMEOUT_SEC` | ComfyUI完了待ちのタイムアウト(秒) | `600.0` |

## アーキテクチャ

- `services/comfyui_client.py`: ComfyUIのHTTP API通信のみを担当（キュー投入・完了待機・ファイル取得・アップロード）
- `services/workflow_builder.py`: `workflows/*.json` テンプレートにパラメータを差し込み、ComfyUI用ワークフロー辞書を生成
- `services/job_runner.py`: ワークフロー投入からファイルダウンロードまでの共通フロー（生成・後処理で共用）
- `services/generation_service.py` / `services/post_process_service.py`: ユースケースごとのオーケストレーション
- `services/agent_service.py` + `services/llm_client.py`: Qwen3.8とのチャットによるプロンプト相談
- `repositories/job_repository.py`: ジョブ履歴のSQLite永続化
- `api/`: FastAPIルーティング層
- `static/`: 簡易UI（画像/動画/アップスケール/補間/相談チャットのタブ切り替え）

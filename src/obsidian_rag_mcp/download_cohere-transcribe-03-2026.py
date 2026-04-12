from huggingface_hub import snapshot_download


# This downloads all model files to a local directory
snapshot_download(
    repo_id="CohereLabs/cohere-transcribe-03-2026",
    local_dir="../../models/cohere-transcribe-03-2026",
    token="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",
    local_dir_use_symlinks=False
# Required since this model has a gateway
)
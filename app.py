from math import ceil

from beam import App, Image, Runtime, Volume
from datasets import DatasetDict, load_dataset

from helpers import base_model, get_newest_checkpoint
from inference import call_model
from training import load_models, train

# ---------------------------------------------------------------------------- #
#                            Beam App Definition                               #
# ---------------------------------------------------------------------------- #
app = App(
    "llama-lora",
    runtime=Runtime(
        cpu=4,
        memory="32Gi",
        gpu="A10G",
        image=Image(
            python_version="python3.10",
            python_packages="requirements.txt",
        ),
    ),
    # Mount Volumes for fine-tuned models and cached model weights
    volumes=[
        Volume(name="checkpoints", path="./checkpoints"),
        Volume(name="pretrained-models", path="./pretrained-models"),
    ],
)


# ---------------------------------------------------------------------------- #
#                                Training API                                  #
# ---------------------------------------------------------------------------- #
@app.run()
def train_model():
    # Trained models will be saved to this path
    beam_volume_path = "./checkpoints"

    # Load dataset -- for this example, we'll use the sahil2801/CodeAlpaca-20k dataset hosted on Huggingface:
    # https://huggingface.co/datasets/sahil2801/CodeAlpaca-20k
    dataset = DatasetDict()
    dataset["train"] = load_dataset("sahil2801/CodeAlpaca-20k", split="train[:20%]")

    # Adjust the training loop based on the size of the dataset
    samples = len(dataset["train"])
    val_set_size = ceil(0.1 * samples)

    train(
        base_model=base_model,
        val_set_size=val_set_size,
        data=dataset,
        output_dir=beam_volume_path,
    )


# ---------------------------------------------------------------------------- #
#                                Inference API                                 #
# ---------------------------------------------------------------------------- #
@app.rest_api()
def run_inference(**inputs):
    # Inputs passed to the API
    input = inputs["input"]

    # Grab the latest checkpoint
    checkpoint = get_newest_checkpoint()

    # Initialize models with latest fine-tuned checkpoint
    models = load_models(checkpoint=checkpoint)

    model = models["model"]
    tokenizer = models["tokenizer"]
    prompter = models["prompter"]

    # Generate text response
    response = call_model(
        input=input, model=model, tokenizer=tokenizer, prompter=prompter
    )
    return response

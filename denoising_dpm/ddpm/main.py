import torch
from tqdm import tqdm
from denoising import DenoiseDiffusion
import typer

# for CLI
app = typer.Typer()

# check if cuda is available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def extract(consts, t):
    c = consts.gather(-1, t)
    return c.reshape(-1, 1, 1, 1)

n_steps = 1000  # T

# load model
PATH = ".\pretrained_weights\celeba.pt"
eps_model = torch.load(PATH)["model_state_dict"]
eps_model.eval()

# instantiate DDPM
diffusion = DenoiseDiffusion(
    eps_model=eps_model,
    n_steps=n_steps,
    device=device,
)

beta = diffusion.beta
alpha = 1.0 - diffusion.beta
alpha_bar = diffusion.alpha_bar
sigma2 = diffusion.beta

# place on device
alpha = alpha.to(device)
sigma2 = sigma2.to(device)

@app.command()
def generate_sample(n_samples: int = 1, n_steps: int = 999, image_channels: int=3, image_size: int=32):
    """Langevin sampling from the diffusion model.

    Args:
        n_samples (int, optional): _description_. Defaults to 1.
        n_steps (int, optional): _description_. Defaults to 999.
        image_channels (int, optional): _description_. Defaults to 3.
        image_size (int, optional): _description_. Defaults to 32.

    Returns:
        torch.Tensor: generated image
    """
    n_samples = n_samples
    image_channels = image_channels
    image_size = image_size
    n_steps = n_steps

    xt = torch.randn([n_samples, image_channels, image_size, image_size], device=device)

    for t_inv in tqdm(range(n_steps)):
        t_ = n_steps - t_inv
        t = xt.new_full((n_samples,), t_, dtype=torch.long)

        with torch.no_grad():
            eps_theta = eps_model(xt, t)

        xt = diffusion.p_sample(xt, t, eps_theta)

    t = xt.new_full((n_samples,), 0, dtype=torch.long)
    alpha_bar = diffusion.alpha_bar
    alpha_bar = extract(alpha_bar, t)
    x0 = (xt - (1 - alpha_bar) ** 0.5 * eps_theta) / (alpha_bar**0.5)

    return {x0}

if __name__ == "__main__":
    app()
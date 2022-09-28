import requests
import torch
import PIL.Image
from torchvision import transforms
from torchvision.transforms.functional import InterpolationMode
from models.blip import blip_decoder


image_size = 480
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def load_demo_image(image_size,device, img_url):

    raw_image = PIL.Image.open(img_url)


    w,h = raw_image.size
    # display(raw_image.resize((w//5,h//5)))
    
    transform = transforms.Compose([
        transforms.Resize((image_size,image_size),interpolation=InterpolationMode.BICUBIC),
        transforms.ToTensor(),
        transforms.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711))
        ]) 
    image = transform(raw_image).unsqueeze(0).to(device)   
    return image


def generate_model():    
    model_url = 'https://storage.googleapis.com/sfr-vision-language-research/BLIP/models/model_base_capfilt_large.pth'    
    # Uncomment below once cloned and above is downloaded once
    # model_url ='model_base_capfilt_large.pth'
    model_caption = blip_decoder(pretrained=model_url, image_size=image_size, vit='base')
    model_caption.eval()
    model_caption = model_caption.to(device)
    return model_caption

def generate_caption(img_url_1):
    model_caption = generate_model()

    image_1 = load_demo_image(image_size=image_size, device=device, img_url=img_url_1)
    
    with torch.no_grad():
        # beam search
        caption = model_caption.generate(image_1, sample=False, num_beams=3, max_length=20, min_length=5) 
        #print('caption: '+caption[0])
        print(caption)


if __name__ == '__main__':
    img_url_1 = '../imagedata/img1.png'
    generate_caption(img_url_1)
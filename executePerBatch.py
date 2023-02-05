import torch, sys, torchvision
from PIL import Image
from dataloader.get import DataGetter
from threading import Thread

sys.path.append('./LAVIS/')
from lavis.models import load_model_and_preprocess

import asyncio
import time

df=DataGetter()
df=df.getData('train')

# set device to cpu 
# device = torch.device("cpu")
device = torch.device("cuda")

model, vis_processors, _ = load_model_and_preprocess(
    name="blip_caption", model_type="base_coco", is_eval=True, device=device
)
vis_processors.keys()

def get_caption(image, model, vis_processors, device):
    return model.generate({
          "image":  vis_processors["eval"](Image.fromarray(image)).unsqueeze(0).to(device)
          }, use_nucleus_sampling=True)


def imageSplitter(lazyimage, model, vis_processors,device) :
    return [ get_caption(im, model, vis_processors,device) for im in lazyimage.load()]


def applyToSeries(nThThread, series, model, vis_processors, device) : 
  print(f"{nThThread}th threads - Apply To Series, from {series.index[0]} to {series.index[-1]}")
  series.apply(lambda x:imageSplitter(x, model, vis_processors, device)).to_csv(
      f"images_captionning_results/from_{series.index[0]}_to_{series.index[-1]}.csv", index_label="index" )
  print(f"Finished {nThThread}th threads.")
    


def prepareTasksLists(serieFull, nTests, batchSize, model, vis_processors, device) : 
    n = serieFull.shape[0] if nTests == -1 else nTests
    serieWork = serieFull.iloc[:n]

    threads=[]
    for batch in range(n//batchSize):
        threads += [
            Thread(target = applyToSeries, args = (batch, serieWork.iloc[batch*batchSize : (batch+1)*batchSize], model, vis_processors, device))
        ]
        if batch % 3 == 0 and batch !=0:
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            threads=[]

    if n%batchSize != 0 :
        last_thread = Thread(target = applyToSeries, args=(n//batchSize, serieWork.iloc[(n//batchSize)*batchSize:], model, vis_processors, device))
        last_thread.start()
        last_thread.join()

#Si fonctionnel éxécuter asyncio.gather sur le retour de prepareTasksLists(df['images'], -1, 370, model, vis_processors)

def main():
    start = time.time()
    print("Starting...")
    nRows = 370
    prepareTasksLists(df['images'], nRows, int(nRows/10), model, vis_processors,device)
    end = time.time()
    print((end - start)/60,"minutes for ", nRows, "rows")
    # await asyncio.gather(*prepareTasksLists(df['images'], -1, 370, model, vis_processors,device))


main()
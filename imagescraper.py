import yaml 
import os 
import glob 
import argparse 
import shutil 
import docker 
from datetime import date

def parse_args(): 
  parser = argparse.ArgumentParser()

  parser.add_argument(
    "filepath", 
    help="the filepath to the base or application folder we are going to update", 
    type=str,
  )

  parser.add_argument(
    "docker_registry", 
    help="the private docker registry where we want to push our images to",
    type=str, 
  )

  return parser.parse_args()

def inplace_change(filename, old_string, new_string):
    # Safely read the input filename using 'with'
    with open(filename) as f:
        s = f.read()
        if old_string not in s:
            print('"{old_string}" not found in {filename}.'.format(**locals()))
            return

    # Safely write the changed content, if found in the file
    with open(filename, 'w') as f:
        print('Changing "{old_string}" to "{new_string}" in {filename}'.format(**locals()))
        s = s.replace(old_string, new_string)
        f.write(s)


def main():

  args = parse_args() 

  docker_client = docker.from_env()
  today = date.today()

  filepath = args.filepath
  docker_registry = args.docker_registry

  filetoparse = (filepath)
  images_list = []

  with open(filetoparse, 'r') as ftp:
        lines = ftp.readlines()

  for line in lines: 
    if "image:" in line or "docker.io" in line and "hub" not in line: 
      if "{{" not in line.lstrip().split(":")[1]: 
        try:    

          docker_image = line.split(" ")[5].strip('\n')

          if docker_image not in images_list:
            images_list.append(docker_image)       

            print("pulling : "  + docker_image)

            if "sha" in docker_image: 

              without_sha = docker_image.split("@")[0]
            
              docker_client.images.pull(docker_image)
              image_to_tag = docker_client.images.get(docker_image)

              image_to_tag.tag(docker_registry + "/" + without_sha + "-" + str(today))
              new_image = docker_registry + "/" + without_sha + "-" + str(today)
              
              inplace_change(filetoparse, docker_image, new_image)

               for log in docker_client.images.push(new_image, stream=True, decode=True): 
                 print(log)

            else: 

              docker_client.images.pull(docker_image)
              image_to_tag = docker_client.images.get(docker_image)

              print(docker_image)

              if ":" not in docker_image: 
                image_to_tag.tag(docker_registry + "/" + docker_image + ":" + str(today)) 
                new_image = docker_registry + "/" + docker_image + ":" + str(today) 
              else: 
                new_image = image_to_tag.tag(docker_registry + "/" + docker_image + "-" + str(today))
                new_image = docker_registry + "/" + docker_image + "-" + str(today) 

              inplace_change(filetoparse, docker_image, new_image)

               for log in docker_client.images.push(new_image, stream=True, decode=True): 
                 print(log)

        except IndexError: 
          pass

if __name__ == "__main__":
  main() 


import random
import asyncio
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from ollama import Client
import io
import base64
import sys

class ShapeGenerator:
    def __init__(self):
        self.client = Client()
        self.shapes_2d = ['circle', 'square', 'triangle']
        self.shapes_3d = ['sphere', 'cube', 'tetrahedron']
        self.colors = ['red', 'green', 'blue', 'yellow', 'purple', 'orange']

    async def generate_shape(self):
        is_3d = random.choice([True, False])
        shape = random.choice(self.shapes_3d if is_3d else self.shapes_2d)
        color = random.choice(self.colors)
        return is_3d, shape, color

    async def generate_code(self, is_3d, shape, color):
        prompt = f"Generate Python code using matplotlib to draw a {color} {shape} in {'3D' if is_3d else '2D'}."
        try:
            response = await self.client.chat(model="llama2", messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ])
            return response['message']['content']
        except Exception as e:
            print(f"Error generating code: {str(e)}")
            if "model 'llama2' not found" in str(e):
                print("The Llama 2 model is not installed. Please run 'ollama pull llama2' to install it.")
                sys.exit(1)
            return None

    async def execute_code(self, code):
        if code is None:
            return None
        try:
            fig = plt.figure()
            if '3d' in code.lower():
                ax = fig.add_subplot(111, projection='3d')
            else:
                ax = fig.add_subplot(111)
            
            exec(code)
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png')
            img_buffer.seek(0)
            img_str = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()
            
            return img_str
        except Exception as e:
            print(f"Error executing code: {str(e)}")
            return None

    async def verify_image(self, img_str, shape, color):
        if img_str is None:
            return False
        prompt = f"Verify if the image contains a {color} {shape}. Respond with 'Yes' if correct, or 'No' with explanation if incorrect."
        try:
            response = await self.client.chat(model="llama2", messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\nImage: {img_str}"
                }
            ])
            return 'yes' in response['message']['content'].lower()
        except Exception as e:
            print(f"Error verifying image: {str(e)}")
            return False

    async def generate_and_verify(self):
        is_3d, shape, color = await self.generate_shape()
        code = await self.generate_code(is_3d, shape, color)
        if code:
            img_str = await self.execute_code(code)
            if img_str:
                is_valid = await self.verify_image(img_str, shape, color)
                
                if is_valid:
                    print(f"Successfully generated and verified a {color} {shape} in {'3D' if is_3d else '2D'}.")
                else:
                    print(f"Failed to generate a valid {color} {shape}. Retrying...")
            else:
                print("Failed to generate image. Retrying...")
        else:
            print("Failed to generate code. Retrying...")

    async def run(self):
        while True:
            try:
                await self.generate_and_verify()
                await asyncio.sleep(5)  # Wait for 5 seconds before generating the next shape
            except KeyboardInterrupt:
                print("\nProgram terminated by user.")
                break
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    generator = ShapeGenerator()
    asyncio.run(generator.run())
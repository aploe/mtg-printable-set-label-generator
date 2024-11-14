from setuptools import setup
from setuptools.command.install import install
import os
import shutil
import pkg_resources

class PostInstallCommand(install):
    def run(self):
        # Run the standard install first
        install.run(self)
        
        # Create user fonts directory if it doesn't exist
        user_fonts_dir = os.path.expanduser('~/.local/share/fonts')
        os.makedirs(user_fonts_dir, exist_ok=True)
        
        # Copy fonts from package to user fonts directory
        try:
            font_files = pkg_resources.resource_listdir('mtglabels', 'fonts')
            for font_file in font_files:
                src = pkg_resources.resource_filename('mtglabels', f'fonts/{font_file}')
                dst = os.path.join(user_fonts_dir, font_file)
                shutil.copy2(src, dst)
            
            # Update font cache
            os.system('fc-cache -f')
        except Exception as e:
            print(f"Warning: Could not install fonts: {e}")

setup(
    cmdclass={
        'install': PostInstallCommand,
    },
)

import os
import platform
import subprocess
import sys
import sysconfig
from distutils import log

from setuptools import Extension, find_packages, setup
from setuptools.command.build_ext import build_ext
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

def detect_installed_cuda_version():
    """Detect installed CUDA version using environment variables."""
    cuda_home = os.environ.get('CUDA_HOME') or os.environ.get('CUDA_PATH')
    
    if cuda_home and os.path.exists(os.path.join(cuda_home, 'version.txt')):
        # Read the CUDA version from the version.txt file in the CUDA installation directory
        try:
            with open(os.path.join(cuda_home, 'version.txt'), 'r') as f:
                version_info = f.read().strip()
                major, minor = version_info.split()[2].split('.')
                return f"+cu{major}"
        except:
            return ""
    else:
        return ""
    
class CMakeExtension(Extension):
    """Extension to integrate CMake build"""
    def __init__(self, name, sourcedir=''):
        super().__init__(name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)

class CMakeBuild(build_ext):
    """Build extension using CMake"""
    user_options = build_ext.user_options + [
        ('cmake-verbose', None, 'Enable verbose output from CMake'),
    ]

    def initialize_options(self):
        build_ext.initialize_options(self)
        self.cmake_verbose = False

    def finalize_options(self):
        build_ext.finalize_options(self)
        self.cmake_verbose = os.getenv('DEBUG', '0') == '1'

        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        cfg = 'Debug' if self.cmake_verbose else 'Release'
        cmake_args = [
            '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir,
            '-DPYTHON_EXECUTABLE=' + sys.executable,
            '-DPYTHON_INCLUDE_DIR=' + sysconfig.get_path('include'),
            '-DCMAKE_BUILD_TYPE=' + cfg,
        ]   
        if os.environ.get('COVERAGE', '0') == '1':
             cmake_args.append('-DCOVERAGE=ON')
        if sysconfig.get_config_var('LIBRARY') is not None:
            cmake_args.append('-DPYTHON_LIBRARY=' + sysconfig.get_config_var('LIBRARY'))
        if 'CC' in os.environ:
            cmake_args.append('-DCMAKE_C_COMPILER=' + os.environ['CC'])
        if 'CXX' in os.environ:
            cmake_args.append('-DCMAKE_CXX_COMPILER=' + os.environ['CXX'])
        if 'CPPFLAGS' in os.environ:
            cmake_args.append('-DCMAKE_CXX_FLAGS=' + os.environ['CPPFLAGS'])
        build_args = ['--config', cfg]
        if self.cmake_verbose:
            cmake_args.append('-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON')
            cmake_args.append('--debug-trycompile')
            build_args.append('--verbose')

        if ('CPU_ONLY' not in os.environ and platform.system() != 'Darwin') or ('CPU_ONLY' in os.environ and os.environ['CPU_ONLY'] != '1'):
            cmake_args.append('-DUSE_CUDA=ON')
            if 'CUDACXX' in os.environ:
                cmake_args.append('-DCMAKE_CUDA_COMPILER=' + os.environ['CUDACXX'])
            
        build_temp = self.build_temp
        if not os.path.exists(build_temp):
            os.makedirs(build_temp)

        # Run cmake configuration
        self.run_subprocess(['cmake', ext.sourcedir] + cmake_args, build_temp)
        # Build the extension
        self.run_subprocess(['cmake', '--build', '.'] + build_args, build_temp)

        self.move_built_library(extdir)
        self.build_info_path = os.path.join(build_temp, 'build_info.txt')
        print(f"Build info path set to: {self.build_info_path}")  # DEBUG: Print to verify the path

    def run_subprocess(self, cmd, cwd):
        log.info('Running command: {}'.format(' '.join(cmd)))
        try:
            subprocess.check_call(cmd, cwd=cwd)
        except subprocess.CalledProcessError as e:
            log.error(f"Command {cmd} failed with error code {e.returncode}")
            log.error(e.output)
            raise

    def move_built_library(self, build_temp):
        built_objects = []
        for root, _, files in os.walk(build_temp):
            for file in files:
                if file.endswith(('.so', '.pyd', '.dll', '.dylib')):
                    built_objects.append(os.path.join(root, file))

        if not built_objects:
            raise RuntimeError(f"Cannot find built library in {build_temp}")
        for built_object in built_objects:
            dest_path = os.path.join(os.path.dirname(__file__), 'gbrl')
            log.info(f'Moving {built_object} to {dest_path}')
            self.copy_file(built_object, dest_path)

class CustomBdistWheel(_bdist_wheel):
    """Custom bdist_wheel to modify the name based on build info"""
    def get_tag(self):
        python_tag, abi_tag, platform_tag = super().get_tag()
       

        return python_tag, abi_tag, platform_tag
    def run(self):
        # Dynamically modify version before running bdist_wheel
        build_ext_cmd = self.get_finalized_command('build_ext')
        # Read the build_info.txt file
        device = ''
        if hasattr(build_ext_cmd, 'build_info_path') and os.path.exists(build_ext_cmd.build_info_path):
            with open(build_ext_cmd.build_info_path, 'r') as f:
                build_info = f.read().strip()
                device = build_info.split('=')[-1]  
                if device != 'cpu':
                    device = f'cu{device}'

        else: 
            device = detect_installed_cuda_version()
        self.distribution.metadata.version = f"{self.distribution.metadata.version}+{device}"
        super().run()

        

setup(
    name="gbrl",
    ext_modules=[CMakeExtension('gbrl/gbrl_cpp', sourcedir='.')],
    cmdclass=dict(build_ext=CMakeBuild, bdist_wheel=CustomBdistWheel),
    packages=find_packages(include=["gbrl"]),  # List of all packages to include
    include_package_data=True,
)

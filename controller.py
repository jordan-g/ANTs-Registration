import numpy as np
import subprocess
import os

initial_moving_transform_lut = {"Geometric Center": 0, "Image Intensities": 1, "Image Origins": 2}

class Controller:
    def __init__(self):
        self.preview_window            = None
        self.fixed_image_path          = None
        self.moving_image_paths        = []
        self.warped_moving_image_paths = []
        self.registration_channel      = 0

        self.params = {"translation": True, "rigid": True, "affine": True, "syn": True, "prefix": "warp_", "initial_moving_transform": "Geometric Center"}

        self.translation_params = {
            "gradient_step": "0.1",
            "metric": "Mutual Information",
            "num_iterations": "200x200x200x0",
            "convergence_threshold": "1e-8",
            "convergence_window_size": "10",
            "shrink_factors": "12x8x4x2",
            "gaussian_sigma": "4x3x2x1"
        }

        self.translation_cross_correlation_params = {
            "metric_weight": "1",
            "radius": "2",
            "sampling_strategy": "None",
            "sampling_percentage": "0.25"
        }

        self.translation_mutual_information_params = {
            "metric_weight": "1",
            "num_bins": "32",
            "sampling_strategy": "Regular",
            "sampling_percentage": "0.25"
        }
        
        self.rigid_params = {
            "gradient_step": "0.1",
            "metric": "Mutual Information",
            "num_iterations": "200x200x200x0",
            "convergence_threshold": "1e-8",
            "convergence_window_size": "10",
            "shrink_factors": "12x8x4x2",
            "gaussian_sigma": "4x3x2x1"
        }

        self.rigid_cross_correlation_params = {
            "metric_weight": "1",
            "radius": "2",
            "sampling_strategy": "None",
            "sampling_percentage": "0.25"
        }

        self.rigid_mutual_information_params = {
            "metric_weight": "1",
            "num_bins": "32",
            "sampling_strategy": "Regular",
            "sampling_percentage": "0.25"
        }

        self.affine_params = {
            "gradient_step": "0.1",
            "metric": "Mutual Information",
            "num_iterations": "200x200x200x0",
            "convergence_threshold": "1e-8",
            "convergence_window_size": "10",
            "shrink_factors": "12x8x4x2",
            "gaussian_sigma": "4x3x2x1"
        }

        self.affine_cross_correlation_params = {
            "metric_weight": "1",
            "radius": "2",
            "sampling_strategy": "None",
            "sampling_percentage": "0.25"
        }

        self.affine_mutual_information_params = {
            "metric_weight": "1",
            "num_bins": "32",
            "sampling_strategy": "Regular",
            "sampling_percentage": "0.25"
        }

        self.syn_params = {
            "gradient_step": "0.1",
            "update_field_variance": "6",
            "total_field_variance": "0",
            "metric": "Cross-Correlation",
            "num_iterations": "200x200x200x200x10",
            "convergence_threshold": "1e-7",
            "convergence_window_size": "10",
            "shrink_factors": "12x8x4x2x1",
            "gaussian_sigma": "4x3x2x1x0"
        }

        self.syn_cross_correlation_params = {
            "metric_weight": "1",
            "radius": "2",
            "sampling_strategy": "None",
            "sampling_percentage": "0.25"
        }

        self.syn_mutual_information_params = {
            "metric_weight": "1",
            "num_bins": "32",
            "sampling_strategy": "Regular",
            "sampling_percentage": "0.25"
        }

        self.shell_command = ""

    def register(self):
        self.create_shell_command()

        if self.shell_command != "":

            self.warped_moving_image_paths = []

            moving_image_path = self.moving_image_paths[self.registration_channel]

            directory       = os.path.dirname(self.fixed_image_path)
            fixed_filename  = os.path.splitext(os.path.basename(self.fixed_image_path))[0]
            moving_filename = os.path.splitext(os.path.basename(moving_image_path))[0]

            warped_moving_image_path = os.path.join(directory, "{}_warped_to_{}.nii.gz".format(moving_filename, fixed_filename))

            with subprocess.Popen(self.shell_command, shell=True, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True) as p:
                for line in p.stdout:
                    print(line, end='') # process line here

            if p.returncode != 0:
                raise subprocess.CalledProcessError(p.returncode, p.args)

             # TODO: warp other channels as well


            self.warped_moving_image_paths.append(warped_moving_image_path)

            self.preview_window.update_warped_moving_image_combobox()
            self.preview_window.show_warped_moving_image()

    def create_shell_command(self):
        if self.fixed_image_path is not None and len(self.moving_image_paths) > 0:
            moving_image_path = self.moving_image_paths[self.registration_channel]

            directory       = os.path.dirname(self.fixed_image_path)
            fixed_filename  = os.path.splitext(os.path.basename(self.fixed_image_path))[0]
            moving_filename = os.path.splitext(os.path.basename(moving_image_path))[0]

            warped_moving_image_path = os.path.join(directory, "{}_warped_to_{}.nii.gz".format(moving_filename, fixed_filename))

            a = warped_moving_image_path.replace(" ", "\ ")
            b = self.fixed_image_path.replace(" ", "\ ")
            c = moving_image_path.replace(" ", "\ ")

            self.shell_command = "antsRegistration -v 1 -d 3 -o [warp_,{}] -n Linear -r [{},{},{}]".format(a, b, c, initial_moving_transform_lut[self.params["initial_moving_transform"]])
            
            if self.params["translation"]:
                self.shell_command += " -t Translation[{}]".format(self.translation_params["gradient_step"])

                if self.translation_params["metric"] == "Cross-Correlation":
                    self.shell_command += " -m CC[{},{},{},{},{},{}]".format(b, c, self.translation_cross_correlation_params["metric_weight"], self.translation_cross_correlation_params["radius"], self.translation_cross_correlation_params["sampling_strategy"], self.translation_cross_correlation_params["sampling_percentage"])
                elif self.translation_params["metric"] == "Mutual Information":
                    self.shell_command += " -m MI[{},{},{},{},{},{}]".format(b, c, self.translation_mutual_information_params["metric_weight"], self.translation_mutual_information_params["num_bins"], self.translation_mutual_information_params["sampling_strategy"], self.translation_mutual_information_params["sampling_percentage"])
                
                self.shell_command += " -c [{},{},{}]".format(self.translation_params["num_iterations"], self.translation_params["convergence_threshold"], self.translation_params["convergence_window_size"])

                self.shell_command += " -f {} -s {}".format(self.translation_params["shrink_factors"], self.translation_params["gaussian_sigma"])

            if self.params["rigid"]:
                self.shell_command += " -t Rigid[{}]".format(self.rigid_params["gradient_step"])

                if self.rigid_params["metric"] == "Cross-Correlation":
                    self.shell_command += " -m CC[{},{},{},{},{},{}]".format(b, c, self.rigid_cross_correlation_params["metric_weight"], self.rigid_cross_correlation_params["radius"], self.rigid_cross_correlation_params["sampling_strategy"], self.rigid_cross_correlation_params["sampling_percentage"])
                elif self.rigid_params["metric"] == "Mutual Information":
                    self.shell_command += " -m MI[{},{},{},{},{},{}]".format(b, c, self.rigid_mutual_information_params["metric_weight"], self.rigid_mutual_information_params["num_bins"], self.rigid_mutual_information_params["sampling_strategy"], self.rigid_mutual_information_params["sampling_percentage"])
                
                self.shell_command += " -c [{},{},{}]".format(self.rigid_params["num_iterations"], self.rigid_params["convergence_threshold"], self.rigid_params["convergence_window_size"])

                self.shell_command += " -f {} -s {}".format(self.rigid_params["shrink_factors"], self.rigid_params["gaussian_sigma"])

            if self.params["affine"]:
                self.shell_command += " -t Affine[{}]".format(self.affine_params["gradient_step"])

                if self.affine_params["metric"] == "Cross-Correlation":
                    self.shell_command += " -m CC[{},{},{},{},{},{}]".format(b, c, self.affine_cross_correlation_params["metric_weight"], self.affine_cross_correlation_params["radius"], self.affine_cross_correlation_params["sampling_strategy"], self.affine_cross_correlation_params["sampling_percentage"])
                elif self.affine_params["metric"] == "Mutual Information":
                    self.shell_command += " -m MI[{},{},{},{},{},{}]".format(b, c, self.affine_mutual_information_params["metric_weight"], self.affine_mutual_information_params["num_bins"], self.affine_mutual_information_params["sampling_strategy"], self.affine_mutual_information_params["sampling_percentage"])
                
                self.shell_command += " -c [{},{},{}]".format(self.affine_params["num_iterations"], self.affine_params["convergence_threshold"], self.affine_params["convergence_window_size"])

                self.shell_command += " -f {} -s {}".format(self.affine_params["shrink_factors"], self.affine_params["gaussian_sigma"])

            if self.params["syn"]:
                self.shell_command += " -t SyN[{},{},{}]".format(self.syn_params["gradient_step"], self.syn_params["update_field_variance"], self.syn_params["total_field_variance"])

                if self.syn_params["metric"] == "Cross-Correlation":
                    self.shell_command += " -m CC[{},{},{},{},{},{}]".format(b, c, self.syn_cross_correlation_params["metric_weight"], self.syn_cross_correlation_params["radius"], self.syn_cross_correlation_params["sampling_strategy"], self.syn_cross_correlation_params["sampling_percentage"])
                elif self.syn_params["metric"] == "Mutual Information":
                    self.shell_command += " -m MI[{},{},{},{},{},{}]".format(b, c, self.syn_mutual_information_params["metric_weight"], self.syn_mutual_information_params["num_bins"], self.syn_mutual_information_params["sampling_strategy"], self.syn_mutual_information_params["sampling_percentage"])
                
                self.shell_command += " -c [{},{},{}]".format(self.syn_params["num_iterations"], self.syn_params["convergence_threshold"], self.syn_params["convergence_window_size"])

                self.shell_command += " -f {} -s {}".format(self.syn_params["shrink_factors"], self.syn_params["gaussian_sigma"])
        else:
            self.shell_command = ""

    def add_moving_images(self, paths):
        self.moving_image_paths += paths

    def remove_moving_image(self, index):
        del self.moving_image_paths[index]

        self.registration_channel = 0

    def add_warped_moving_images(self, paths):
        self.warped_moving_image_paths += paths

    def remove_warped_moving_image(self, index):
        del self.warped_moving_image_paths[index]
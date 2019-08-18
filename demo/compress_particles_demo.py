import pyapr
import numpy as np


def main():
    # Read in an image

    io_int = pyapr.filegui.InteractiveIO()

    apr = pyapr.APR()
    parts = pyapr.ShortParticles()

    # Initialize APRFile for I/O
    aprfile = pyapr.io.APRFile()
    aprfile.set_read_write_tree(True)

    fpath_apr = io_int.get_apr_file_name()

    # Write APR and particles to file
    aprfile.open(fpath_apr, 'READ')
    aprfile.read_apr(apr)
    aprfile.read_particles(apr, 'particles', parts)

    original_file_size = aprfile.current_file_size_MB()
    aprfile.close()

    pyapr.viewer.interactive_compression(apr, parts)

    fpath_apr_save = io_int.save_apr_file_name()

    aprfile.open(fpath_apr_save, 'WRITE')
    aprfile.write_apr(apr)  # need to write the unchanged apr structure
    aprfile.write_particles('particles', parts)

    compressed_file_size = aprfile.current_file_size_MB()

    aprfile.close()

    original_image_size = 2*pow(10, -6)*apr.x_num(apr.level_max())*apr.y_num(apr.level_max())*apr.z_num(apr.level_max())

    print("Original File Size: {:7.2f} MB".format(original_file_size))
    print("Lossy Compressed File Size: {:7.2f} MB".format(compressed_file_size))

    print("Original Memory Compression Ratio: {:7.2f} ".format(original_image_size/original_file_size))
    print("Lossy Memory Compression Ratio: {:7.2f} ".format(original_image_size/compressed_file_size))

if __name__ == '__main__':
    main()
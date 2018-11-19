# Starts an instance of tshark to visualize traffic
# I've already installed tshark on the VM

# The following will print all TCP traffic on port 3005
# Run this in a separate shell window
# Packet capture starts with "Capturing on ens160"
sudo tshark -i ens160 -Y "tcp.port == 3005"
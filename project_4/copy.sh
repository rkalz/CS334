# To both connect to Github AND 138.26.64.46 without a password
# You'll need to setup an SSH key
# In lan.cs.uab.edu, call
#   ssh-keygen -t rsa -b 4096 -C "your-github@email.com"
# Keep pressing enter until done
# Then, do the following (this will make sure you can't accidentally
# delete your key)
#   eval "$(ssh-agent -s)"
#   ssh-add ~/.ssh/id-rsa

# First, we're going to add the SSH key to Github so we can pull
# the repo. To get our public key, call
#   cat ~/.ssh/id_rsa.pub
# This key should start with "ssh-rsa" and end with your email
# Copy this key, then go to 
#   Github -> Settings -> SSH and GPG keys -> New SSH key
# Name the key whatever, paste it, and enter your password
# Now you can pull from Github without a password!
# To make sure it worked, in lan.cs.uab.edu, enter
#   git clone git@github.com:rkalz/CS334.git

# Now, we're going to give the same key to 138.26.64.46 
# so we can connect to it without a password
# From lan.cs.uab.edu, call
#   ssh-copy-id -i .ssh/id_rsa.pub group01@138.26.64.46
# Enter the password (QDxkCubq)
# You should now be able to connect to 138.26.64.46
# without a password (try it)

# All done! Since these VMs are shared between all of us
# I've already made the keys for connecting from group01
# to the VM. The following script, launched from 
# lan.cs.uab.edu, should work now

cd CS334
git pull
cd ..
scp -r CS334/ group01@138.26.64.46:
ssh group01@138.26.64.46 "scp -r CS334/ student@192.168.1.100:"

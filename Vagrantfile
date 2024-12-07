###############################################################################
#
# Ragit Vagrant machine
#
# This Vagrantfile set up a development environment with Ubuntu 22.04, Python,
# PostgreSQL, Vim with clipboard support, and custom dotfiles.
#
# The setup script also ensures the environment is ready to sync and use a
# shared directory from the host machine, with compatibility for both Windows
# and Unix-like systems.
#
# The purpose of this Vagrant VM is to be used mostly for development purposes.
#
###############################################################################

$script = <<SCRIPT
sudo apt update
sudo apt install python3-pip -y
sudo apt-get install libpq-dev python3-dev -y
mkdir -p /home/vagrant/ragit-data
chown vagrant:vagrant /home/vagrant/ragit-data
sudo apt install postgresql postgresql-contrib -y
sudo apt install poppler-utils -y
sudo chown vagrant:vagrant /home/vagrant/.bashrc
echo "export PYTHONPATH='/vagrant' " >> /home/vagrant/.bashrc
echo "alias pt=/vagrant/pt.sh" >> /home/vagrant/.bashrc
echo "alias ragit='python3 /vagrant/ragit/backend/ragit_cmd.py'" >> /home/vagrant/.bashrc
SCRIPT


USER_NAME = ENV['USER'] || ENV['USERNAME']

Vagrant.configure("2") do |config|
      # Use the official Bento Ubuntu 22.04 base box
      config.vm.box = "bento/ubuntu-22.04"

      # Provision the VM using the defined script.
      config.vm.provision "shell", inline: $script

      # Provision the postgres db from a separate script file
      config.vm.provision "shell", path: "install-psql.sh"

      # Enable SSH agent and X11 forwarding for clipboard sharing
      config.ssh.forward_agent = true # Used for Clipboard sharing.
      config.ssh.forward_x11 = true # Used for Clipboard sharing.

      # Forward ragit's UI port from guest to host
      config.vm.network "forwarded_port", guest: 13131, host: 13132

      # Set the correct host path format based on the host OS.
      if Vagrant::Util::Platform.windows?
            # Is Windows, set the path using Windows-style backslashes.
            host_path = "C:\\Users\\#{USER_NAME}\\ragit-data"
      else
            # Not Windows (assuming Linux/Mac), use Unix-style forward slashes.
            host_path = "/home/#{USER_NAME}/ragit-data"
      end
      config.vm.synced_folder host_path, "/home/vagrant/ragit-data"

      # Specify VM provider.
      config.vm.provider "virtualbox" do |vb|
        vb.name = "adapt_aware_ragit"
        vb.memory = 8192
        vb.cpus = 2
        # Used for Clipboard sharing.
        vb.customize ['modifyvm', :id, '--clipboard', 'bidirectional']
      end

      # Set the VM hostname
      config.vm.hostname = "ragit"
end

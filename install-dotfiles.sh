#!/bin/bash
##############################################################################
#  Installs vim with clipboard support and dotfiles.
##############################################################################

cd /home/vagrant

# Install requirements.txt
sudo pip3 install -r /vagrant/requirements.txt
# install vim gtk to make clipboard interaction simpler.
cd
sudo apt update
sudo apt-get purge vim
sudo apt-get autoremove
sudo apt update
sudo apt install xclip -y
sudo apt install vim-gtk3 -y

# Clone dotfiles if needed

DOTFILES_DIR=/home/vagrant/dotfiles
if [ ! -d "$DOTFILES_DIR" ]; then
  cd /home/vagrant
  git clone https://github.com/codingismycraft/dotfiles.git
  sudo chown -R vagrant:vagrant /home/vagrant/dotfiles
  cd dotfiles
  ./install_light.sh /home/vagrant
  cd
fi

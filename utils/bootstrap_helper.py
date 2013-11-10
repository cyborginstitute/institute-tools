import os
from files import symlink
from shutil import rmtree

reset_ref = None

def init_fs(buildsystem):
    fab_dir = 'fabfile'

    if os.path.islink(fab_dir):
        os.remove(fab_dir)
    elif os.path.isdir(fab_dir):
        rmtree(fab_dir)

    symlink('fabfile', os.path.join(buildsystem, 'fabsrc'))

    symlink(name=os.path.join(buildsystem, 'fabsrc', 'utils'),
            target=os.path.join(os.path.abspath(buildsystem), 'utils'))

    symlink(name=os.path.join(buildsystem, 'stats', 'utils'),
            target=os.path.join(os.path.abspath(buildsystem), 'utils'))

    symlink(name=os.path.join(buildsystem, 'fabsrc', 'stats'),
            target=os.path.join(os.path.abspath(buildsystem), 'stats'))

    # copyfile(src=os.path.join(os.path.abspath(buildsystem), 'bin', 'bootstrap.py'),
    #          dst=os.getcwd())

def clean_buildsystem(buildsystem, conf):
    if os.path.islink('fabfile'):
        os.remove('fabfile')
        print('[bootstrap-clean]: removed fabfile symlink')

    if os.path.exists(buildsystem):
        rmtree(buildsystem)
        print('[bootstrap-clean]: purged %s' % buildsystem)

def bootstrap():
    """
    The bootstrap file calls this function. Use this as a site for future
    extension.
    """
    print('[bootstrap]: initialized fabfiles and dependencies. Regenerate buildsystem now.')

def main():
    bootstrap()

if __name__ == '__main__':
    main()

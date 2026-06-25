import ftplib
import os

FTP_HOST = "ftpupload.net"
FTP_USER = "if0_42129168"
FTP_PASS = "2NEBtsBiGlAwB"

def upload_dir(ftp, local_dir, remote_dir):
    try:
        ftp.mkd(remote_dir)
    except:
        pass
    
    ftp.cwd(remote_dir)
    
    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        if os.path.isfile(local_path):
            print(f"Uploading {local_path} to {item}...")
            with open(local_path, 'rb') as f:
                ftp.storbinary(f'STOR {item}', f)
        elif os.path.isdir(local_path):
            print(f"Creating directory {item}...")
            upload_dir(ftp, local_path, item)
            ftp.cwd("..")

def main():
    print("Connecting to FTP...")
    ftp = ftplib.FTP()
    ftp.connect(FTP_HOST, 21, timeout=30)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.set_pasv(True)
    
    print("Connected. Uploading files...")
    ftp.cwd("/htdocs")
    
    local_bot_dir = r"c:\Users\User\Desktop\fas foood\php-bot"
    local_webapp_dir = r"c:\Users\User\Desktop\fas foood\webapp"
    
    # Upload php-bot files
    for item in os.listdir(local_bot_dir):
        local_path = os.path.join(local_bot_dir, item)
        if os.path.isfile(local_path):
            print(f"Uploading {item}...")
            with open(local_path, 'rb') as f:
                ftp.storbinary(f'STOR {item}', f)
        elif os.path.isdir(local_path):
            upload_dir(ftp, local_path, item)
            ftp.cwd("/htdocs")
            
    # Upload webapp files to /htdocs/webapp
    print("Uploading webapp...")
    upload_dir(ftp, local_webapp_dir, "webapp")
            
    print("Upload complete!")
    ftp.quit()

if __name__ == "__main__":
    main()

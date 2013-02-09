rsync -avz -e ssh -f"- .*" -f"- rsync_this.sh" -f"+ *" ./ $1

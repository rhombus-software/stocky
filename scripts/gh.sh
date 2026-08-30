echo "Uses Github CLI and Gh auth"

commit(){
    cd .. && git commit -m "$1" && git add . && git push
}
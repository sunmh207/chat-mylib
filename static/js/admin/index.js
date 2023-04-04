function confirmDel(id){
  if (confirm("确定要删除文件吗？")) {
    window.location.href="/del_file?id="+id;
  }else{
    return;
  }
}


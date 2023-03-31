var currentPage = 1;
var pageSize = 10;
$(document).ready(function() {
  getUserList(currentPage, pageSize);
});
function getUserList(pageIndex, pageSize) {
  $.ajax({
    url: '/files?page=' + pageIndex + '&size=' + pageSize,
    type: 'GET',
    success: function(data) {
      // 清空文件列表
      $('#file-table tbody').empty();

      // 填充用户列表
      for (var i = 0; i < data.items.length; i++) {
        var resource = data.items[i];
        var row = '<tr><td>' + resource.id + '</td><td>' + resource.name + '</td><td width="200">' + resource.updated_time + '</td><td width="65"> <a href="#" onclick=confirmDel("'+ resource.id + '")>删除</a></td></tr>';
        $('#file-table tbody').append(row);
      }

      // 更新分页栏
      /*
      currentPage = data.pageIndex;
      pageSize = data.pageSize;
      var totalPage = Math.ceil(data.totalCount / pageSize);
      var pagination = '<ul class="pagination">';
      if (currentPage > 1) {
        pagination += '<li class="page-item"><a class="page-link" href="#" onclick="getUserList(' + (currentPage - 1) + ',' + pageSize + ')">上一页</a></li>';
      }
      for (var i = 1; i <= totalPage; i++) {
        if (i == currentPage) {
          pagination += '<li class="page-item active"> <a  class="page-link" >' + i + '</a></li>';
        } else {
          pagination += '<li class="page-item"><a class="page-link" href="#" onclick="getUserList(' + i + ',' + pageSize + ')">' + i + '</a></li>';
        }
      }
      if (currentPage < totalPage) {
        pagination += '<li class="page-item"><a class="page-link" href="#" onclick="getUserList(' + (currentPage + 1) + ',' + pageSize + ')">下一页</a></li>';
      }
      pagination += '</ul>';
      $('#pagination').html(pagination);
      */
    }
  });
}

function confirmDel(id){
  if (confirm("确定要删除文件吗？")) {
    window.location.href="/delfile?id="+id;
  }else{
    return;
  }
}
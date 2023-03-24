from mylib.service.mysql_service import MySQLService

if __name__ == '__main__':
    conn = MySQLService().get_connection()
    cursor = conn.cursor()
    sql = "insert into resource(id, name, summary, type, created_time, updated_time) values (%s, %s, %s, %s, %s, %s)"
    try:
        cursor.execute(sql, ('xxxx2', 'stanley', 'this is summary', 'pdf', 1679578922,1679578922))
        conn.commit()
        print("添加成功")
    except Exception as e:
        conn.rollback()
        print("添加失败")

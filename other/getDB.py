f = open("data.txt", "r")
database = []
for line in f:
    try:
        line_split = line.split(":")
        login = line_split[0]
        line_split = line_split[4].split(",")
        year = line_split[1]
        name = line_split[0]
        data = []
        data.append(login)
        data.append(year)
        data.append(name)
        database.append(data)
    except IndexError:
        continue
f.close()
f = open("database.sql", "w")
f.write("USE `rubbergod`;\n")
f.write("INSERT INTO `bot_valid_persons`(\n")
f.write("`login`,\n")
f.write("`name`,\n")
f.write("`year`,\n")
f.write("`status`\n)\n")
f.write("VALUES\n")
string = ""
for data in database:
    string = string + "(\n"
    string = string + "'" + data[0] + "',\n"
    string = string + "'" + data[2] + "',\n"
    string = string + "'" + data[1] + "',\n"
    string = string + "1" + "\n"
    string = string + "),\n"
string = string[:-2]
string = string + ";\n"
f.write(string)

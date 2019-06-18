f = open("data.txt", "r")
database = []
for line in f:
    if "FIT" in line:
        try:
            line = line.split(":")
            login = line[0]
            line = line[4]
            line = line.split(',')
            year = line[1]
            name = line[0]
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
f.write("`year`\n)\n")
f.write("VALUES\n")
string = ""
for line in database:
    string = string + "(\n"
    string = string + "'" + line[0] + "',\n"
    string = string + "'" + line[2] + "',\n"
    string = string + "'" + line[1] + "'\n"
    string = string + "),\n"
string = string[:-2]
string = string + ";\n"
f.write(string)

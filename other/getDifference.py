# this file should be a dump of the current database
f = open("database_backup.sql", "r")
old_logins = []
for line in f:
    if "INSERT INTO `bot_valid_persons`" in line:
        entries = line.split("),(")
        for entry in entries:
            login = entry.split("'")[1]
            old_logins.append(login)
f.close()

# this file should be the /etc/passwd from eva / merlin
# (with '|grep /homes' recommended)
f = open("data.txt", "r")
database_new = []
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
        database_new.append(data)
    except IndexError:
        continue
f.close()

database = []
for data in database_new:
    if data[0] not in old_logins:
        # for now that the new students are just added in as 1BIT
        if "FIT BIT 1r" in data[1]:
            data[1] = data[1].replace("1r", "0r")
        database.append(data)

f = open("database_difference.sql", "w")
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

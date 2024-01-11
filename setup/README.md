# Additional setup steps

> Useful on bot migration and when you want to setup and run some less ordinary commands.

## SSH keys for `/ios` & `/verify_db pull`

These commands need to connect to school servers `merlin` and/or `eva` to gather necessary information. Since this is a potential security risk, it's done with SSH keys which have only specific commands allowed to minimize that risk.

Because this is more advanced stuff, we created a bash script to do most of the work for you: `./ssh_keygen.sh`. But since systems are fragile and these things break from time to time, it is advised that you look into it, understand what it does before running it and if necessary, run the commands yourself if it doesn't work (we hope it does)

The script generates the necessary keys exactly where bot expects them (Docker setup only) and prints them out to `stdout`. You then need to connect to `merlin` (or `eva`, these two share your `$HOME`), create `.ssh` folder and `authorized_keys` file in it with the right permissions, then append the script output to this file.

```bash
mkdir -p -m 750 ~/.ssh
install -m 740 ~/.ssh/authorized_keys
echo >> $_ << EOF
<script_output>
EOF
```

# vstask without dependencies

[vstask](https://github.com/cmccandless/vstask/), is a Python tool for running tasks in VS Code's tasks.json file from from the command line.

I really want it available as a system command, so that I don't need to set up pipenv before running it. I would be much easier if vstask has no dependencies, but it has 3 in it's requirements.txt.

```
flake8==3.5.0
pytest==3.6.3
coveralls>=1.2.0
```

But all 3 of these are used for development and shouldn't be needed for running the code.

---

After fiddling with this for a little while, I realized that requirements.txt is for the development requirements and install_requires in setup.py is for the tool's requirements.

```
install_requires=[],
```

Whoops.

![](images/XKCD_1053_ten_thousand.png)


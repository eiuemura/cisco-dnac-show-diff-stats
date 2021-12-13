# cisco-dnac-show-diff-stats
---

## Why?
I hope that this sample code helps people create tools and then reduce the time to find the problem by visualizing increasing the latest error counter.

A sample code will also help you understand the command runner, one of the DNAC API features, and Genie parser.

## Technologies & Frameworks Used

This is Cisco Sample Code!

**Cisco Products & Services:**

- Cisco DNA Center
  - https://sandboxdnac.cisco.com (or use your own)


**Tools & Frameworks:**

- Python3
- Genie: Command paser(pyATS)
- Matplotlib: Visualization with Python

## Installation

```
git clone git clone https://github.com/eiuemura/cisco-dnac-show-diff-stats
```

```
pip install -r requirements.txt
```

## Running the code

```python3 show_diff_stats.py```


### Trouble shooting
If you found the following error, this command can fix the problem.


TypeError: Couldn't find foreign struct converter for 'cairo.Context'

```
sudo apt-get install python3-gi-cairo
```

### Sample Screenshot

![](./img/movie01.gif)
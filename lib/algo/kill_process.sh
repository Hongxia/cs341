#!/bin/bash
kill -9 $(ps aux | grep '[p]ython' | awk '{print $2}')
ps aux | grep '[p]ython'
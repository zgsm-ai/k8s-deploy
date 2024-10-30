#!/bin/sh

function usage() {
    echo "resolve-vars.sh [-f input-filename] [-o output-filename] [-h]"
    echo "  input-filename: 输入文件名，如果未指定，则处理当前目录下所有.yaml,.yml,.conf文件，包括子目录"
    echo "  output-filename: 输出文件名，如果未指定，则直接修改输入文件"
    echo "resolve-vars.sh从apisix.conf.sh文件读取配置项"
    echo "  由{{和}}括起来的变量varname，将.替换为varname的变量值"
}

while getopts "f:o:h" opt
do
    case $opt in
        f)
        input=$OPTARG;;
        o)
        output=$OPTARG;;
        h)
        usage
        exit 0;;
        ?)
        usage
        exit 1;;
    esac
done

. ./apisix.conf.sh

function resolve_file() {
    input_file=$1
    output_file=$2
    cp -f $input_file $output_file
    echo generate $input_file to $output_file ...

    # 查询所有{{变量}}，并进行值替换
    for i in `grep -o -w -E "\{\{([[:alnum:]]|\.|_)*\}\}" $output_file|sort|uniq|tr -d '\r'`; do
        # 提取键名 
        key=${i:2:(${#i}-4)}
        # 获取键值：查找文件内容
        value=$(eval echo \$$key)
        echo "$key=>$value"
        # 替换文件内容
        if echo "$value" | grep -vq '#'; then
            sed -i "s#$i#$value#g" $output_file;
        elif echo "$value" | grep -vq '/'; then
            sed -i "s/$i/$value/g" $output_file;
        elif echo "$value" | grep -vq ','; then
            sed -i "s,$i,$value,g" $output_file;
        else
            echo "$value中同时包含特殊字符“#/,”，无法执行替换"
        fi
    done
}

function resolve_dir() {
    # 目录路径
    dir="$1"
    echo generate $dir ...

    for entry in "$dir"/*; do
        if [ -d "$entry" ]; then
            # 如果是目录，则递归调用
            resolve_dir "$entry"
        elif [ -f "$entry" ] && [[ "$entry" == *.tpl ]]; then
            # 如果是 .tpl 文件，去掉后缀并输出文件名
            filename="${entry%.tpl}"  # 去掉 .tpl 后缀
            # 输出去掉后缀的文件名
            resolve_file "$entry" "$filename"
        fi
    done
}

if [ ""X == "$output"X ]; then
    output="$input"
fi

# 用户输入参数
echo input: $input
echo output: $output

if [ X"" == X"$input" ]; then
    resolve_dir .
else
    resolve_file $input $output
    cat $output
fi

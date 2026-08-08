# cft-data-prepare

[cft](https://github.com/788009/cft) 的数据准备脚本。

## 使用方法

1. 克隆本仓库并安装依赖。

    ```bash
    git clone https://github.com/788009/cft-data-prepare.git
    cd cft-data-prepare
    pip install pandas
    ```

2. 在 `prepare/data.csv` 中填入实际数据，格式如下：

    ```
    no,name,short,university,province,city,contact
    1,张S,ZS,南京大学,江苏,南京,电话 - 13987654321
    2,李S,LS,北京理工大学,北京,北京,QQ - 1234567890
    ```

    - 大学名称必须为全名。
    - `contact` 不一定与上述格式相同，实际只是字符串，若为空，前端会自动隐藏该项。

    可以让 AI 转换原始数据，提示词示例：

    ```
    （实际数据，如从表格复制粘贴）

    将以上内容改成 CSV，其中 name 列将姓名的第二个字变成首字母缩写，short 列将整个名字变成首字母缩写，格式参考

    no,name,short,university,province,city,contact
    1,张S,ZS,南京大学,江苏,南京,电话 - 13987654321
    2,李S,LS,北京理工大学,北京,北京,QQ - 1234567890
    3,王W,WW,香港中文大学(深圳),广东,深圳,
    ```

3. 查看 `prepare/` 下的其他文件，按照实际情况修改，其中
    - `guide.md` 是使用说明
    - `message.md` 会显示在设置面板的最后
    - `middle_school_info.json` 控制中学卡片的信息
    - `teachers.md` 是教师信息。

4. 运行 `prepare.py`。

    ```bash
    python prepare.py
    ```

生成的 `data/` 文件夹可以直接复制到 cft 项目根目录。

## 数据来源

- GeoJSON 原始数据来自 [GeoMapData_CN](https://github.com/lyhmyd1211/GeoMapData_CN)，使用 [mapshaper](https://mapshaper.org/) 统一地区边界。
- 十段线数据来自 [geojson.cn](https://geojson.cn/)
- 大学经纬度数据
    - 大陆学校大部分来自 [china-university-location](https://github.com/flwfdd/china-university-location)，中国人民解放军信息工程大学数据来自[维基百科](https://en.wikipedia.org/wiki/PLA_Information_Engineering_University)
    - 港澳台地区数据大部分来自[这篇文章](https://blog.csdn.net/cold_long/article/details/102966505)，香港中文大学、香港理工大学、香港科技大学数据来自 Google Maps
- 省市区 adcode 数据来自 [AreaCity-JsSpider-StatsGov](https://github.com/xiangyuecn/AreaCity-JsSpider-StatsGov)

## 许可证

MIT License

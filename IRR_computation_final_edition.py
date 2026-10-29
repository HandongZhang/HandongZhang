import asyncio
import io
import os
import shutil
import datetime
import nest_asyncio
import pandas as pd
import numpy as np
import xlwings as xw
from playwright.async_api import async_playwright

# 允许在已有事件循环中嵌套运行
nest_asyncio.apply()

# ================================
# 1. 数据抓取（异步）
# ================================
async def fetch_cffex_data():
    """异步抓取中金所可交割券及转换因子，返回字典 {品种: DataFrame}"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        page = await browser.new_page()
        await page.goto("http://www.cffex.com.cn/cn/kjggzxx.html", wait_until="networkidle")
        await page.wait_for_selector("table.kjggzxx-table", timeout=10000)

        select_element = page.locator("select#product")
        options = select_element.locator("option")
        option_count = await options.count()
        varieties = []
        for i in range(option_count):
            text = await options.nth(i).inner_text()
            varieties.append(text.strip())
        print("找到品种选项：", varieties)

        variety_data = {}
        for var in varieties:
            print(f"正在切换品种：{var}")
            await select_element.select_option(var)
            await page.wait_for_function(
                "document.querySelector('table.kjggzxx-table tbody tr') !== null",
                timeout=5000
            )
            await page.wait_for_timeout(800)

            # 提取合约代码（转换因子列名）
            header_instruments = page.locator(
                "table.kjggzxx-table thead tr:nth-child(2) td[data-bind]"
            )
            instrument_names = []
            for j in range(await header_instruments.count()):
                instrument_names.append((await header_instruments.nth(j).inner_text()).strip())
            print(f"  合约代码：{instrument_names}")

            table_html = await page.locator("table.kjggzxx-table").inner_html()
            dfs = pd.read_html(io.StringIO(f"<table>{table_html}</table>"))
            if not dfs:
                print(f"  警告：品种 {var} 未读取到表格，跳过")
                continue
            df = dfs[0]

            base_columns = [
                "国债全称", "银行间代码", "上交所代码", "深交所代码",
                "到期日", "票面利率(%)"
            ]
            manual_columns = base_columns + instrument_names

            if df.shape[1] == len(manual_columns):
                df.columns = manual_columns
            else:
                print(f"  警告：品种 {var} 列数不匹配，实际 {df.shape[1]} 列，预期 {len(manual_columns)} 列")
                if df.shape[1] > len(manual_columns):
                    df = df.iloc[:, :len(manual_columns)]
                df.columns = manual_columns[:df.shape[1]]

            # 添加后缀
            df["银行间代码"] = df["银行间代码"].astype(str).apply(
                lambda x: f"{x}.IB" if x not in ("--", "", "nan") else x
            )
            df["上交所代码"] = df["上交所代码"].astype(str).apply(
                lambda x: f"{x}.SH" if x not in ("--", "", "nan") else x
            )
            df["深交所代码"] = df["深交所代码"].astype(str).apply(
                lambda x: f"{x}.SZ" if x not in ("--", "", "nan") else x
            )
            rename_dict = {old: f"{old}.CFE" for old in instrument_names if old in df.columns}
            df.rename(columns=rename_dict, inplace=True)

            variety_data[var] = df
            print(f"  已抓取 {var}：{len(df)} 条记录")

        await browser.close()
        return variety_data


def save_factor_data(data_dict, path="转换因子数据1.xlsx"):
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for variety, df in data_dict.items():
            df.to_excel(writer, sheet_name=variety, index=False)
    print(f"转换因子数据已保存至 {path}")


# ================================
# 2. 更新底稿与指标
# ================================
def update_workbooks(factor_path, indicator_path, draft_path):
    backup_factor = factor_path.replace('.xlsx', '_备份.xlsx')
    backup_indicator = indicator_path.replace('.xlsx', '_备份.xlsx')
    backup_draft = draft_path.replace('.xlsx', '_备份.xlsx')

    # 确保备份文件的目录存在（如果路径包含目录）
    for p in [backup_factor, backup_indicator, backup_draft]:
        dir_name = os.path.dirname(p)
        if dir_name:   # 只有当目录非空时才创建
            os.makedirs(dir_name, exist_ok=True)

    print("正在打开工作簿...")
    org_dta = xw.Book(factor_path)
    指标 = xw.Book(indicator_path)
    底稿 = xw.Book(draft_path)

    print("正在创建备份...")
    org_dta.save(backup_factor)
    指标.save(backup_indicator)
    底稿.save(backup_draft)
    print("备份完成。")

    # 更新底稿
    print("开始更新底稿...")
    for i in range(len(底稿.sheets)):
        target_sheet = 底稿.sheets[i]
        sheet_name = target_sheet.name
        if sheet_name.startswith('TS'):
            src_idx = 0
        elif sheet_name.startswith('TF'):
            src_idx = 1
        elif sheet_name.startswith('TL'):
            src_idx = 3
        else:
            src_idx = 2

        source_sheet = org_dta.sheets[src_idx]
        source_col = source_sheet.range('B2').expand('down').value
        if not isinstance(source_col, list):
            source_col = [source_col]

        last_row_old = target_sheet.range('A' + str(target_sheet.cells.last_cell.row)).end('up').row
        if last_row_old >= 3:
            target_sheet.range(f'A3:A{last_row_old}').clear_contents()

        start_row = 3
        target_sheet.range(f'A{start_row}').value = [[x] for x in source_col]
        new_rows = len(source_col)
        last_row_new = start_row + new_rows - 1

        if last_row_new > start_row:
            start_col = 2
            end_col = 16
            source_range = target_sheet.range((start_row, start_col), (start_row, end_col))
            target_range = target_sheet.range((start_row, start_col), (last_row_new, end_col))
            source_range.api.AutoFill(target_range.api)

        print(f"  底稿工作表 '{sheet_name}' 更新完成，共 {new_rows} 行。")

    底稿.app.calculate()
    print("底稿计算完成。")

    # 更新指标
    print("开始更新指标...")
    for i in range(len(指标.sheets)):
        target_sheet = 指标.sheets[i]
        sheet_name = target_sheet.name
        if sheet_name.startswith('TS'):
            src_idx = 0
        elif sheet_name.startswith('TF'):
            src_idx = 1
        elif sheet_name.startswith('TL'):
            src_idx = 3
        else:
            src_idx = 2

        source_sheet = org_dta.sheets[src_idx]
        source_col = source_sheet.range('B2').expand('down').value
        if not isinstance(source_col, list):
            source_col = [source_col]

        last_row_old = target_sheet.range('F' + str(target_sheet.cells.last_cell.row)).end('up').row
        if last_row_old >= 12:
            target_sheet.range(f'F12:F{last_row_old}').value = None

        start_row = 12
        target_sheet.range(f'F{start_row}').value = [[x] for x in source_col]
        new_rows = len(source_col)
        last_row_new = start_row + new_rows - 1

        if last_row_new > start_row:
            start_col_g = 7
            end_col_p = 16
            try:
                target_sheet.range((start_row, start_col_g), (last_row_new, end_col_p)).api.UnMerge()
            except:
                pass
            template_formulas = target_sheet.range((start_row, start_col_g), (start_row, end_col_p)).formula
            target_sheet.range((start_row, start_col_g), (last_row_new, end_col_p)).formula = template_formulas

        print(f"  指标工作表 '{sheet_name}' 更新完成，共 {new_rows} 行。")

    指标.app.calculate()
    print("指标计算完成。")

    # 重命名工作表
    for sheet1 in 底稿.sheets:
        contract_name = sheet1.range('B2').value
        if contract_name:
            try:
                sheet1.name = contract_name
            except Exception as e:
                print(f"重命名工作表 {sheet1.name} 失败: {e}")

    for sheet2 in 指标.sheets:
        contract_name = sheet2.range('D12').value
        if contract_name:
            try:
                sheet2.name = contract_name
            except Exception as e:
                print(f"重命名工作表 {sheet2.name} 失败: {e}")

    底稿.save()
    指标.save()
    org_dta.close()
    指标.close()
    底稿.close()

    return backup_indicator


# ================================
# 3. 公式转值（修正版：直接遍历单元格）
# ================================
def convert_formulas_to_values(file_path, save_as_new=True):
    app = xw.App(visible=False, add_book=False)
    wb = None
    try:
        wb = app.books.open(file_path)
        if wb is None:
            print(f"❌ 无法打开文件：{file_path}，可能被占用或不存在")
            return None

        for sheet in wb.sheets:
            print(f"正在处理工作表: {sheet.name}")
            used_range = sheet.used_range
            if used_range is None:
                continue

            # 直接遍历每个单元格
            for cell in used_range:
                try:
                    if cell is None:
                        continue
                    if cell.merge_cells:
                        merge_area = cell.merge_area
                        if merge_area is None:
                            continue
                        top_left = sheet.cells(merge_area.row, merge_area.column)
                        if top_left is not None and top_left.formula and top_left.formula.startswith('='):
                            top_left.value = top_left.value
                    else:
                        if cell.formula and cell.formula.startswith('='):
                            cell.value = cell.value
                except Exception:
                    # 忽略单个单元格错误，继续
                    pass

        if save_as_new:
            new_file = file_path.replace('.xlsx', '_converted.xlsx')
            wb.save(new_file)
            print(f"✅ 转换成功！新文件保存为：{new_file}")
            return new_file
        else:
            wb.save()
            print(f"✅ 转换成功！已覆盖原文件：{file_path}")
            return file_path
    except Exception as e:
        print(f"❌ 转换失败：{e}")
        return None
    finally:
        if wb:
            try:
                wb.close()
            except:
                pass
        app.quit()


# ================================
# 4. 筛选 IRR 前4（增加文件占用处理）
# ================================
def filter_top4_by_irr(converted_file, output_file="清洗后_结果.xlsx"):
    all_sheets = pd.read_excel(converted_file, sheet_name=None, header=[10])
    results = {}

    for sheet_name, df_raw in all_sheets.items():
        print(f"正在处理 Sheet: {sheet_name}")
        df_raw = df_raw.loc[:, ~df_raw.columns.str.contains('^Unnamed')]
        df_raw = df_raw.replace(0, np.nan)
        df_raw['期货合约'] = df_raw['期货合约'].ffill()
        cols = ['结算价，元', '周涨跌', '持仓量，手', '周变化']
        df_raw[cols] = df_raw[cols].ffill()

        df_top4 = (
            df_raw
            .sort_values(['期货合约', 'IRR,%'], ascending=[True, False], na_position='last')
            .groupby('期货合约')
            .head(4)
            .reset_index(drop=True)
        )
        results[sheet_name] = df_top4

    # 处理文件占用
    if os.path.exists(output_file):
        try:
            os.remove(output_file)
            print(f"已删除旧文件：{output_file}")
        except PermissionError:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_file.replace('.xlsx', f'_{timestamp}.xlsx')
            print(f"文件被占用，将使用新文件名：{output_file}")

    with pd.ExcelWriter(output_file) as writer:
        for sheet_name, df in results.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"筛选结果已保存至 {output_file}")
    return output_file


# ================================
# 5. 合并所有 Sheet
# ================================
def merge_sheets_to_first(file_path):
    backup_path = file_path.replace('.xlsx', '_backup.xlsx')
    shutil.copy2(file_path, backup_path)
    print(f"已备份到：{backup_path}")

    app = xw.App(visible=False, add_book=False)
    wb = app.books.open(file_path)
    target_sheet = wb.sheets[0]

    app_bak = xw.App(visible=False, add_book=False)
    wb_bak = app_bak.books.open(backup_path)
    all_data = []
    for idx, sheet_bak in enumerate(wb_bak.sheets):
        if idx == 0:
            continue
        used = sheet_bak.used_range
        last_row = used.last_cell.row
        last_col = used.last_cell.column
        if last_row >= 2:
            data = sheet_bak.range((2, 1), (last_row, last_col)).value
            if data:
                if isinstance(data[0], list):
                    all_data.extend(data)
                else:
                    all_data.append(data)
    wb_bak.close()
    app_bak.quit()

    if all_data:
        next_row = target_sheet.used_range.last_cell.row + 1
        target_sheet.range((next_row, 1)).value = all_data
        print(f"追加了 {len(all_data)} 行数据。")

    header = target_sheet.range('1:1').value[0]
    cols_to_merge = []
    for i, cell in enumerate(header):
        if cell:
            cell_str = str(cell)
            if any(key in cell_str for key in ['期货合约', '券', '合约']) and '交割券' not in cell_str:
                cols_to_merge.append(i+1)
            elif '结算价' in cell_str:
                cols_to_merge.append(i+1)
            elif '持仓量' in cell_str:
                cols_to_merge.append(i+1)
            elif '周涨跌' in cell_str:
                cols_to_merge.append(i+1)
            elif '周变化' in cell_str:
                cols_to_merge.append(i+1)
    if not cols_to_merge:
        print("警告：未找到标准列，使用默认 [1,9,10,11,12]")
        cols_to_merge = [1, 9, 10, 11, 12]

    total_rows = target_sheet.used_range.last_cell.row
    if total_rows >= 2:
        data_rows = total_rows - 1
        group_size = 4
        num_groups = data_rows // group_size
        for g in range(num_groups):
            start_row = 2 + g * group_size
            end_row = start_row + group_size - 1
            for col in cols_to_merge:
                try:
                    target_sheet.range((start_row, col), (end_row, col)).unmerge()
                except:
                    pass
                target_sheet.range((start_row, col), (end_row, col)).merge()
        print(f"共处理 {num_groups} 组，每组 {group_size} 行。")

    wb.save()
    wb.close()
    app.quit()
    print("合并完成。")


# ================================
# 6. 拆分
# ================================
def split_into_sheets(file_path, output_file="拆分后_结果.xlsx"):
    group_size = 12
    sheet_names = ['TS', 'TF', 'T', 'TL']
    merge_group_size = 4

    app = xw.App(visible=False, add_book=False)
    wb = app.books.open(file_path)
    src_sheet = wb.sheets[0]
    used_range = src_sheet.used_range
    full_data = used_range.value
    if not full_data or len(full_data) < 2:
        raise ValueError("源表没有数据或只有标题行。")

    header = list(full_data[0])
    data_all = full_data[1:]
    total_data_rows = len(data_all)

    if total_data_rows % group_size != 0:
        print(f"警告：数据行数 {total_data_rows} 不是 {group_size} 的倍数，截取前 {total_data_rows - total_data_rows % group_size} 行。")
        data_all = data_all[: total_data_rows - total_data_rows % group_size]
        total_data_rows = len(data_all)

    data_all = [list(row) if isinstance(row, (list, tuple, np.ndarray)) else [row] for row in data_all]

    cols_to_merge = []
    for i, cell in enumerate(header):
        if cell is None:
            continue
        cell_str = str(cell)
        if ('期货合约' in cell_str or cell_str == '合约') and '交割券' not in cell_str:
            cols_to_merge.append(i+1)
        elif '结算价' in cell_str:
            cols_to_merge.append(i+1)
        elif '持仓量' in cell_str:
            cols_to_merge.append(i+1)
        elif '周涨跌' in cell_str:
            cols_to_merge.append(i+1)
        elif '周变化' in cell_str:
            cols_to_merge.append(i+1)
    if not cols_to_merge:
        print("未匹配到标准列，使用默认 [1,9,10,11,12]")
        cols_to_merge = [1, 9, 10, 11, 12]

    new_app = xw.App(visible=False, add_book=True)
    new_wb = new_app.books.add()
    while len(new_wb.sheets) > 1:
        new_wb.sheets[-1].delete()
    first_sheet = new_wb.sheets[0]

    num_groups = total_data_rows // group_size
    if num_groups > len(sheet_names):
        print(f"警告：组数 {num_groups} 超过名称数 {len(sheet_names)}，只处理前 {len(sheet_names)} 组。")
        num_groups = len(sheet_names)

    for g in range(num_groups):
        start = g * group_size
        end = start + group_size
        group_data = data_all[start:end]
        content = [header] + group_data

        if g == 0:
            new_sheet = first_sheet
            new_sheet.name = sheet_names[g]
        else:
            new_sheet = new_wb.sheets.add(name=sheet_names[g])

        new_sheet.range('A1').value = content

        total_rows = len(content)
        if total_rows > 1:
            data_start_row = 2
            num_merge_blocks = (total_rows - 1) // merge_group_size
            for mb in range(num_merge_blocks):
                start_row = data_start_row + mb * merge_group_size
                end_row = start_row + merge_group_size - 1
                for col in cols_to_merge:
                    try:
                        new_sheet.range((start_row, col), (end_row, col)).unmerge()
                    except:
                        pass
                    new_sheet.range((start_row, col), (end_row, col)).merge()

    for sheet in new_wb.sheets:
        if sheet.name not in sheet_names[:num_groups]:
            sheet.delete()

    new_wb.save(output_file)
    new_wb.close()
    new_app.quit()
    wb.close()
    app.quit()
    print(f"拆分完成！结果已保存至：{output_file}")
    return output_file


# ================================
# 主流程
# ================================
def main():
    # ===== 请根据您的实际目录修改 base_dir =====
    base_dir = r'E:/HuaweiMoveData/Users/Zhd/Desktop/国债期货指标测算'

    factor_file = "转换因子数据1.xlsx"                     # 抓取生成，位于当前工作目录
    indicator_file = os.path.join(base_dir, "国债期货关键指标测算_30-6-2026.xlsx")
    draft_file = os.path.join(base_dir, "数据底稿.xlsx")

    # 检查必要文件是否存在
    for f in [indicator_file, draft_file]:
        if not os.path.exists(f):
            print(f"错误：文件不存在 - {f}")
            print("请检查 base_dir 是否正确，或确认文件名称是否一致。")
            return

    print("=== 步骤1: 抓取中金所数据 ===")
    loop = asyncio.get_event_loop()
    data_dict = loop.run_until_complete(fetch_cffex_data())
    if not data_dict:
        print("抓取失败，退出。")
        return

    # ---------- 处理文件占用 ----------
    if os.path.exists(factor_file):
        try:
            os.remove(factor_file)
            print(f"已删除旧文件：{factor_file}")
        except PermissionError:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            factor_file = f"转换因子数据_{timestamp}.xlsx"
            print(f"文件被占用，将使用新文件名：{factor_file}")

    save_factor_data(data_dict, factor_file)

    print("\n=== 步骤2: 更新底稿与指标 ===")
    backup_indicator = update_workbooks(factor_file, indicator_file, draft_file)

    print("\n=== 步骤3: 转换公式为数值 ===")
    converted_file = convert_formulas_to_values(backup_indicator, save_as_new=True)
    if not converted_file:
        print("转换失败，退出。")
        return

    print("\n=== 步骤4: 筛选 IRR 前4 ===")
    filtered_file = filter_top4_by_irr(converted_file, "清洗后_结果.xlsx")

    print("\n=== 步骤5: 合并所有 Sheet ===")
    merge_sheets_to_first(filtered_file)

    print("\n=== 步骤6: 拆分到 TS/TF/T/TL ===")
    final_file = split_into_sheets(filtered_file, "拆分后_结果.xlsx")

    print(f"\n✅ 全部完成！最终结果文件：{final_file}")

    # ---------- 清理中间文件 ----------
    backup_indicator_file = indicator_file.replace('.xlsx', '_备份.xlsx')
    backup_draft_file = draft_file.replace('.xlsx', '_备份.xlsx')
    backup_factor_file = factor_file.replace('.xlsx', '_备份.xlsx')

    intermediate_files = [
        factor_file,
        backup_indicator,
        converted_file,
        filtered_file,
        filtered_file.replace('.xlsx', '_backup.xlsx'),
        backup_indicator_file,
        backup_draft_file,
        backup_factor_file,
    ]
    # 去重并过滤掉最终结果文件
    intermediate_files = list(set(intermediate_files))
    for f in intermediate_files:
        if os.path.exists(f) and f != final_file:
            try:
                os.remove(f)
                print(f"已删除中间文件：{f}")
            except Exception as e:
                print(f"删除 {f} 失败：{e}")

    print("清理完成，仅保留最终结果。")


if __name__ == "__main__":
    main()

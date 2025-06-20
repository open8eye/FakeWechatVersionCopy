import requests
import re
import os
import sys
import json
import logging
from git import Repo

current_directory = os.path.dirname(os.path.realpath(sys.argv[0]))


class GiteeRepository:
    """Gitee 仓库操作类，封装克隆、拉取、提交、推送等功能"""

    def __init__(self, gitee_url: str, local_path: str, branch: str = "main",
                 auth_method: str = "ssh", token: str = None,
                 username: str = None, password: str = None):
        """
        初始化 Gitee 仓库操作对象

        参数:
            gitee_url: Gitee 仓库 URL（支持 https 和 ssh 格式）
            local_path: 本地仓库路径
            branch: 操作的分支名，默认为 "main"
            auth_method: 认证方式，可选值: "ssh", "token", "password"
            token: Gitee 私人令牌（当 auth_method 为 "token" 时使用）
            username: 用户名（当 auth_method 为 "password" 时使用）
            password: 密码（当 auth_method 为 "password" 时使用）
        """
        self.gitee_url = gitee_url
        self.local_path = local_path
        self.branch = branch
        self.auth_method = auth_method
        self.token = token
        self.username = username
        self.password = password
        self.repo = None

        # 配置日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # 处理认证后的 URL
        self._process_auth_url()

    def _process_auth_url(self):
        """处理认证方式，生成带认证信息的 URL"""
        if self.auth_method == "token" and self.token:
            if "https://" in self.gitee_url:
                self.auth_url = self.gitee_url.replace("https://", f"https://{self.token}@")
            else:
                self.logger.warning("令牌认证需要使用 HTTPS 格式的 URL")
                self.auth_url = self.gitee_url
        elif self.auth_method == "password" and self.username and self.password:
            if "https://" in self.gitee_url:
                self.auth_url = self.gitee_url.replace("https://", f"https://{self.username}:{self.password}@")
            else:
                self.logger.warning("密码认证需要使用 HTTPS 格式的 URL")
                self.auth_url = self.gitee_url
        else:
            self.auth_url = self.gitee_url  # 默认使用原始 URL（SSH 不需要额外处理）

    def _get_repo(self) -> Repo:
        """获取本地仓库对象，如果不存在则克隆"""
        if self.repo:
            return self.repo

        # 检查本地仓库是否存在
        repo_exists = os.path.exists(self.local_path) and os.path.isdir(os.path.join(self.local_path, ".git"))

        if repo_exists:
            self.logger.info(f"使用已存在的本地仓库: {self.local_path}")
            self.repo = Repo(self.local_path)
        else:
            self.logger.info(f"克隆远程仓库到: {self.local_path}")
            self.repo = Repo.clone_from(self.auth_url, self.local_path, branch=self.branch)

        return self.repo

    def clone(self) -> bool:
        """克隆仓库到本地"""
        try:
            if os.path.exists(self.local_path):
                self.logger.error(f"本地路径 {self.local_path} 已存在")
                return False

            Repo.clone_from(self.auth_url, self.local_path, branch=self.branch)
            self.logger.info(f"成功克隆仓库: {self.gitee_url}")
            return True
        except Exception as e:
            self.logger.error(f"克隆失败: {str(e)}")
            return False

    def pull(self) -> bool:
        """从远程仓库拉取最新代码"""
        try:
            repo = self._get_repo()

            # 切换到指定分支
            if self.branch not in [b.name for b in repo.branches]:
                self.logger.info(f"本地不存在分支 {self.branch}，尝试从远程拉取")
                repo.git.checkout("-b", self.branch, f"origin/{self.branch}")
            else:
                repo.git.checkout(self.branch)

            # 拉取更新
            origin = repo.remote("origin")
            origin.pull(self.branch)
            self.logger.info(f"成功拉取分支 {self.branch} 的更新")
            return True
        except Exception as e:
            self.logger.error(f"拉取失败: {str(e)}")
            return False

    def commit(self, message: str = "Auto commit", files: list = None) -> bool:
        """提交本地更改

        参数:
            message: 提交信息
            files: 要提交的文件列表，默认为提交所有更改
        """
        try:
            repo = self._get_repo()

            # 添加文件到暂存区
            if not files:
                self.logger.info("未指定文件，将提交所有更改")
                repo.git.add(all=True)
            else:
                for file_path in files:
                    repo.git.add(file_path)

            # 检查是否有更改需要提交
            if repo.is_dirty(untracked_files=True):
                repo.git.commit("-m", message)
                self.logger.info(f"提交成功: {message}")
                return True
            else:
                self.logger.info("没有更改需要提交")
                return False
        except Exception as e:
            self.logger.error(f"提交失败: {str(e)}")
            return False

    def push(self) -> bool:
        """推送本地分支到远程仓库"""
        try:
            repo = self._get_repo()

            # 切换到指定分支
            repo.git.checkout(self.branch)

            # 推送
            origin = repo.remote("origin")
            if not repo.active_branch.tracking_branch():
                origin.push(set_upstream_to=f"origin/{self.branch}")
            else:
                origin.push()

            self.logger.info(f"成功推送分支 {self.branch} 到远程")
            return True
        except Exception as e:
            self.logger.error(f"推送失败: {str(e)}")
            return False

    def commit_and_push(self, message: str = "Auto commit", files: list = None) -> bool:
        """提交并推送本地更改

        参数:
            message: 提交信息
            files: 要提交的文件列表，默认为提交所有更改
        """
        try:
            if self.commit(message, files):
                return self.push()
            return True  # 如果没有更改需要提交，也认为操作成功
        except Exception as e:
            self.logger.error(f"提交并推送失败: {str(e)}")
            return False


def printf(text, color=31):
    print(f"\033[{color}m{text}\033[0m")


# 获取最新版本号
def get_wx_version_latest():
    result = None
    response = requests.get("https://api.github.com/repos/tom-snow/wechat-windows-versions/releases",
                            timeout=5)  # 设置超时时间为5秒
    if response.status_code == 200:
        releases = response.json()
        result = releases[0].get("tag_name", "3.9.12.51")
        printf(f"获取版本信息成功: {result[1:]}")
    return result[1:]


def save_file(content, file_path, mode="w", encoding="utf-8"):
    """
    将内容保存到文件

    参数:
        content (str/bytes): 需要保存的内容（文本或二进制数据）
        file_path (str): 文件保存路径
        mode (str): 打开文件的模式（默认"w"，写入文本）
        encoding (str): 文件编码（默认"utf-8"，二进制模式下忽略）

    返回:
        None
    """
    try:
        with open(file_path, mode, encoding=encoding if "b" not in mode else None) as f:
            f.write(content)
        print(f"文件已成功保存到 {file_path}")
    except Exception as e:
        print(f"保存文件时出错: {e}")


def read_json_file(file_path: str) -> dict | None:
    """
    读取 JSON 文件并返回解析后的数据

    Args:
        file_path: JSON 文件的路径

    Returns:
        解析后的 JSON 数据（字典格式），如果读取失败则返回 None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"文件未找到: {file_path}")
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}")
    except Exception as e:
        print(f"读取 JSON 文件时发生错误: {e}")
    return None


def get_config(repo, config_path):
    # 更新或者克隆仓库
    if os.path.exists(config_path):
        repo.pull()
    else:
        repo.clone()
    if not os.path.exists(config_path):
        printf("配置文件不存在")
        return None
    return read_json_file(config_path)


try:
    remote_version = get_wx_version_latest()
    print(remote_version)
    fake_wechat_version_copy_path = os.path.join(current_directory, "gitee/FakeWechatVersionCopy")
    # 令牌认证方式
    repo = GiteeRepository(
        gitee_url="https://gitee.com/lulendi/FakeWechatVersionCopy.git",
        local_path=fake_wechat_version_copy_path,
        branch="main",
        auth_method="token",
        token="30eb3360b5fe75359efa3dd27c863186"
    )
    config_path = os.path.join(fake_wechat_version_copy_path, "config.json")
    config = get_config(repo, config_path)
    local_version = config.get("version", "3.9.12.51")
    # 更新版本号
    if local_version != remote_version:
        local_versions = re.findall(r'\d', local_version)
        remote_versions = re.findall(r'\d', remote_version)
        if remote_versions > local_versions:
            result = remote_version
            config['version'] = result
            save_file(config, config_path)
            print(f"保存文件成功")
            repo.commit_and_push(message=f"自动更新版本号: {result}", files=[config_path])

except Exception as e:
    printf(f'获取版本信息失败: {e}')

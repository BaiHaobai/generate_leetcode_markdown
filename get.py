import requests, json, re
from requests_toolbelt import MultipartEncoder
import os
import time, random
import string

user_agent = r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'


class getLeetcode():
    def __init__(self):
        self.session = requests.Session()
        self.csrftoken = ''
        self.is_login = False

    def login(self, username, password):
        url = 'https://leetcode-cn.com/problemset/all/'
        # url = 'https://leetcode.com'
        cookies = self.session.get(url).cookies
        for cookie in cookies:
            if cookie.name == 'csrftoken':
                self.csrftoken = cookie.value

        url = "https://leetcode-cn.com/accounts/login"
        # url = "https://leetcode.com/accounts/login/"

        params_data = {
            'csrfmiddlewaretoken': self.csrftoken,
            'login': username,
            'password': password,
            'next': '/problemset'
        }
        headers = {
            'User-Agent': user_agent,
            'Connection': 'keep-alive',
            'Referer': 'https://leetcode-cn.com/accounts/login/',
            "origin": "https://leetcode-cn.com"
        }
        # headers = {
        #     'User-Agent': user_agent,
        #     'Connection': 'keep-alive',
        #     'Referer': 'https://leetcode.com/accounts/login/',
        #     "origin": "https://leetcode.com"
        # }
        m = MultipartEncoder(params_data)

        headers['Content-Type'] = m.content_type
        self.session.post(url,
                          headers=headers,
                          data=m,
                          timeout=10,
                          allow_redirects=False)
        self.is_login = self.session.cookies.get('LEETCODE_SESSION') != None
        return self.is_login

    def get_problems(self):

        # url = "https://leetcode-cn.com/api/problems/all/"
        url = "https://leetcode.com/api/problems/all/"

        headers = {'User-Agent': user_agent, 'Connection': 'keep-alive'}
        resp = self.session.get(url, headers=headers, timeout=10)

        question_list = json.loads(resp.content.decode('utf-8'))
        question_resp = []
        for question in question_list['stat_status_pairs']:
            question_temp = {}

            question_title = question['stat']['question__title']
            question_id = question['stat']['question_id']

            question_slug = question['stat']['question__title_slug']

            question_status = question['status']

            level = question['difficulty']['level']
            if question_status == 'ac':
                question_temp['question_title'] = question_title
                question_temp['question_id'] = question_id
                question_temp['question_slug'] = question_slug
                question_temp['level'] = level
                question_resp.append(question_temp)
        return question_resp

    def get_problem_data(self, slug):

        url = "https://leetcode-cn.com/graphql"
        problem_data_resp = {}
        params = {
            "operationName":
            "questionData",
            "variables": {
                "titleSlug": slug
            },
            "query":
            '''query questionData($titleSlug: String!) {
                    question(titleSlug: $titleSlug) {
                        translatedTitle
                        translatedContent
    					questionFrontendId
                        title
                        }
                    } '''
        }

        json_data = json.dumps(params).encode('utf8')

        headers = {
            'User-Agent': user_agent,
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode-cn.com/problemsset/all/'
        }
        resp = self.session.post(url,
                                 data=json_data,
                                 headers=headers,
                                 timeout=10)
        translatedtitle = resp.json()['data']['question']['translatedTitle']
        content = resp.json()['data']['question']['translatedContent']
        id = resp.json()['data']['question']['questionFrontendId']
        title = resp.json()['data']['question']['title']
        problem_data_resp['translatedtitle'] = translatedtitle
        problem_data_resp['content'] = content
        problem_data_resp['id'] = id
        problem_data_resp['title'] = title
        problem_data_resp['slug'] = slug
        return problem_data_resp

    def get_submissions(self, slug):
        # url = "https://leetcode-cn.com/graphql"
        url = "https://leetcode.com/graphql"
        params = {
            'operationName':
            "Submissions",
            'variables': {
                "offset": 0,
                "limit": 40,
                "lastKey": '',
                "questionSlug": slug
            },
            'query':
            '''query Submissions($offset: Int!, $limit: Int!, $lastKey: String, $questionSlug: String!) {
                        submissionList(offset: $offset, limit: $limit, lastKey: $lastKey, questionSlug: $questionSlug) {
                        submissions {
                            statusDisplay
                            lang
                            url
                            __typename
                        }
                        __typename
                    }
                }'''
        }

        json_data = json.dumps(params).encode('utf8')

        headers = {
            'User-Agent': user_agent,
            'Connection': 'keep-alive',
            'Referer': 'https://leetcode-cn.com/problems/two-sum/submissions/',
            "Content-Type": "application/json"
        }
        resp = self.session.post(url,
                                 data=json_data,
                                 headers=headers,
                                 timeout=10)
        content = resp.json()
        sub_res = {}
        print(content)
        for submission in content['data']['submissionList']['submissions']:
            if submission['lang'] == 'python' and submission[
                    'statusDisplay'] == 'Accepted':
                sub_res['python'] = submission['url']
            elif submission['lang'] == 'javascript' and submission[
                    'statusDisplay'] == 'Accepted':
                sub_res['javascript'] = submission['url']
        return sub_res

    def get_submission_code(self, sub_url):
        # url = "https://leetcode-cn.com" + sub_url
        url = "https://leetcode.com" + sub_url
        headers = {
            'User-Agent': user_agent,
            'Connection': 'keep-alive',
            "Content-Type": "application/json"
        }
        code_content = self.session.get(url, headers=headers, timeout=10)
        pattern = re.compile(
            r'submissionCode: \'(?P<code>.*)\',\n  editCodeUrl', re.S)
        m1 = pattern.search(code_content.text)
        code = m1.groupdict()['code'].encode('utf-8').decode(
            'unicode_escape') if m1 else None
        return code

    def generate_question(self, problem, submission):
        path = 'D:\github'
        fileName = "{}. {}".format(problem['id'], problem['slug'])
        jscode, pythoncode = None, None
        if 'javascript' in submission:
            jscode = self.get_submission_code(submission['javascript'])
        if 'python' in submission:
            pythoncode = self.get_submission_code(submission['python'])
        if os.path.isfile(
                os.path.join(path, 'leetcode', 'problems', fileName + ".md")):
            print(problem['translatedtitle'] + '已存在！')
            return
        else:
            with open(os.path.join(path, 'leetcode', 'problems',
                                   fileName + ".md"),
                      'w',
                      encoding='utf-8') as f:

                f.write("# 题目地址\n")
                f.write("https://leetcode.com/problems/" + problem['slug'] +
                        "/\n\n")
                f.write("https://leetcode-cn.com/problems/" + problem['slug'] +
                        "/\n")

                f.write("# 题目描述\n")
                f.write("## {}.{}\n".format(problem['id'],
                                            problem['translatedtitle']))
                if problem['content'] != None:
                    f.write(problem['content'])
                else:
                    f.write('付费题目')
                    print("{}. {}".format(problem['id'], problem['title']))
                f.write("\n")
                f.write("# 思路\n\n")

                f.write("# 代码\n")
                f.write("Python Code:\n\n")
                f.write("```\n")
                if pythoncode:
                    f.write(pythoncode)
                f.write("\n```\n")
                f.write("JavaScript Code:\n\n")
                f.write("```\n")
                if jscode:
                    f.write(jscode)
                f.write("\n```\n")
        print(problem['translatedtitle'] + '生成结束！')


if __name__ == "__main__":
    s = getLeetcode()
    s.get_submissions('two-sum')
    # if s.login('wu-wu-lu-lu', 'Zxcvbht123'):
    #     questions_list = s.get_problems()
    #     print(questions_list)
    # else:
    #     print('密码错误')
    # if s.login('bht251595339@gmail.com', 'zxcvbht123'):
    #     questions_list = s.get_problems()
    #     for question in questions_list:
    #         s.generate_question(s.get_problem_data(question['question_slug']),
    #                             s.get_submissions(question['question_slug']))
    #         time.sleep(random.randint(1, 3))
    # else:
    #     print('密码错误')
    # s.generate_question()

class Node:
    def __init__(self, token):
        self.token = token
        self.leftSubtree = None
        self.rightSubtree = None

class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop()

    def peek(self):
        return self.items[-1]

    def is_empty(self):
        return len(self.items) == 0

def create_expression_tree(postfix):
    stack = Stack()
    for token in postfix.split():
        if token.isdigit():
            node = Node(token)
            stack.push(node)
        else:
            right = stack.pop()
            left = stack.pop()
            node = Node(token)
            node.rightSubtree = right
            node.leftSubtree = left
            stack.push(node)
    return stack.pop()

def inorder_traversal(node):
    if node:
        inorder_traversal(node.leftSubtree)
        print(node.token, end=' ')
        inorder_traversal(node.rightSubtree)

def preorder_traversal(node):
    if node:
        print(node.token, end=' ')
        preorder_traversal(node.leftSubtree)
        preorder_traversal(node.rightSubtree)

def postorder_traversal(node):
    if node:
        postorder_traversal(node.leftSubtree)
        postorder_traversal(node.rightSubtree)
        print(node.token, end=' ')

def evaluate_expression_tree(node):
    if node:
        if node.token.isdigit():
            return int(node.token)
        else:
            left = evaluate_expression_tree(node.leftSubtree)
            right = evaluate_expression_tree(node.rightSubtree)
            if node.token == '+':
                return left + right
            elif node.token == '-':
                return left - right
            elif node.token == '*':
                return left * right
            elif node.token == '/':
                if right == 0:
                    raise ValueError("Division by zero")
                return left / right

def get_height(node):
    if node is None:
        return 0
    else:
        left_height = get_height(node.leftSubtree)
        right_height = get_height(node.rightSubtree)
        return max(left_height, right_height) + 1

def balance_factor(node):
    if node is None:
        return 0
    else:
        return get_height(node.leftSubtree) - get_height(node.rightSubtree)

def main():
    expression_tree = None
    while True:
        print("\nMenu:")
        print("1. พี่แทนตั้งโจทย์ (สร้าง Expression Tree จาก Postfix)")
        print("2. แปลงโจทย์ให้พี่อู๋อ่านง่าย (Infix พร้อมวงเล็บ)")
        print("3. สลับสไตล์โจทย์แบบพี่แทน (Prefix)")
        print("4. ยืนยันโจทย์ต้นฉบับ (Postfix)")
        print("5. กรรมการเฉลยคําตอบ (Evaluate)")
        print("6. เช็คว่าโจทย์ยาก/สมดุลแค่ไหน (Balance Factor)")
        print("7. ยกเลิกศึกนี้ / ออกจากโปรแกรม")
        choice = input("เลือกเมนู (1-7): ")

        if choice == '1':
            postfix = input("ป้อนนิพจน์ postfix: ")
            try:
                expression_tree = create_expression_tree(postfix)
                print("ต้นไม้ Expression Tree ได้สร้างแล้ว")
            except Exception as e:
                print(e)

        elif choice == '2':
            if expression_tree:
                print("Inorder Traversal (Infix): ", end='')
                inorder_traversal(expression_tree)
                print()
            else:
                print("พี่แทนยังไม่ได้ตั้งโจทย์ กรุณาเลือกเมนู 1 ก่อน")

        elif choice == '3':
            if expression_tree:
                print("Preorder Traversal (Prefix): ", end='')
                preorder_traversal(expression_tree)
                print()
            else:
                print("พี่แทนยังไม่ได้ตั้งโจทย์ กรุณาเลือกเมนู 1 ก่อน")

        elif choice == '4':
            if expression_tree:
                print("Postorder Traversal (Postfix): ", end='')
                postorder_traversal(expression_tree)
                print()
            else:
                print("พี่แทนยังไม่ได้ตั้งโจทย์ กรุณาเลือกเมนู 1 ก่อน")

        elif choice == '5':
            if expression_tree:
                try:
                    result = evaluate_expression_tree(expression_tree)
                    print("ค่าที่คำนวณได้: ", result)
                except:
                    print("เกิดข้อผิดพลาดในการคำนวณ")
            else:
                print("พี่แทนยังไม่ได้ตั้งโจทย์ กรุณาเลือกเมนู 1 ก่อน")

        elif choice == '6':
            if expression_tree:
                bf = balance_factor(expression_tree)
                if bf == 0:
                    print("ต้นไม้สมดุล")
                else:
                    print(f"ต้นไม้ไม่สมดุล ค่า Balance Factor = {bf}")
            else:
                print("พี่แทนยังไม่ได้ตั้งโจทย์ กรุณาเลือกเมนู 1 ก่อน")

        elif choice == '7':
            print("ออกจากโปรแกรม")
            break

        else:
            print("กรุณาเลือกเมนู 1-7 เท่านั้น")

if __name__ == "__main__":
    main()

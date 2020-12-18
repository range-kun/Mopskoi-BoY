from random import randint
from itertools import cycle
from abc import ABCMeta, abstractmethod


class SpotOccupied(Exception):
    def __str__(self):
        return 'Точка занята'


class BoardOut(Exception):
    def __str__(self):
        return 'Точка корабля за пределами доски'


class BeenShot(Exception):
    def __str__(self):
        return 'В данную точку уже стреляли'


class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.condition = '■'

    def __repr__(self):
        return 'self.condition'

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    #  сделал что бы попробовать :)
    def __setattr__(self, attr, value):
        if attr == 'condition':
            self.__dict__[attr] = value
        elif value >= 0:
            self.__dict__[attr] = value
        else:
            raise AttributeError(attr + ' должень быть больше 0')


class Ship:
    def __init__(self, start, length, direction):
        self.start = start
        self.length = length
        self.direction = direction
        self.lives = length
        self.contour = []

    @property
    def ship_locat(self):
        if self.direction == 0:
            ship_coordinates = [Dot(self.start.x + i, self.start.y) for i in range(self.length)]
        else:
            ship_coordinates = [Dot(self.start.x, self.start.y + i) for i in range(self.length)]
        return ship_coordinates


class Board:
    def __init__(self, size):
        self.size = size
        self.field = [['O'] * size for _ in range(size)]
        self.enemy_field = [['O'] * size for _ in range(size)]
        self.dots_around = ((-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1))
        self.hidden = False
        self.occupied = []
        self.ships = []
        self.lives = 0

    def add_ship(self, ship):
        self.check_ship(ship)
        for dot in ship.ship_locat:
            x, y = dot.x, dot.y
            self.field[x][y] = dot.condition
            self.occupied.append(dot)
        self.ships.append(ship)

    def check_ship(self, ship):
        for dot in ship.ship_locat:
            x, y = dot.x, dot.y
            self.check_dot(dot.x, dot.y, start_point=True)
            for dx, dy in self.dots_around:
                x_1 = x + dx
                y_1 = y + dy
                self.check_dot(x_1, y_1, ship=ship)

    def check_dot(self, x, y, start_point=False, ship=None):
        if start_point and self.out_of_board(x, y):  # если стартовая точка выходит за
            raise BoardOut()  # пределы то ошибка
        elif self.out_of_board(x, y):
            return
        elif Dot(x, y) in self.occupied:
            raise SpotOccupied()
        elif ship:
            ship.contour.append((x, y))

    def out_of_board(self, x, y):
        return not 0 <= x < self.size or not 0 <= y < self.size

    def make_contour(self, ship):
        for x, y in ship.contour:
            if self.field[x][y] == 'O':
                self.field[x][y] = 'T'
                self.enemy_field[x][y] = 'T'

    def shoot(self, dot):
        try:
            self.check_dot(dot.x, dot.y, start_point=True)
        except SpotOccupied:
            if dot.condition == 'X':
                raise BeenShot()
            dot.condition = 'X'
            self.field[dot.x][dot.y] = dot.condition
            self.enemy_field[dot.x][dot.y] = dot.condition
            for ship in self.ships:
                if dot in ship.ship_locat:
                    ship.lives -= 1
                    if ship.lives > 0:
                        return 'Ранил'
                    else:
                        self.make_contour(ship)
                        return 'Убил'
        else:
            if self.field[dot.x][dot.y] != 'O':
                raise BeenShot()
            self.field[dot.x][dot.y] = 'T'
            self.enemy_field[dot.x][dot.y] = 'T'
            return 'Мимо!'

    def __repr__(self):
        repra = '  | 1 | 2 | 3 | 4 | 5 | 6 |\n'
        field = self.enemy_field if self.hidden else self.field
        for number, value in enumerate(field):
            repra += f'{number + 1}  | ' + ' | '.join(value) + ' |\n'
        return repra


class Player:
    __metaclass__ = ABCMeta

    def __init__(self, our, not_our, lives):
        self.our_board = our
        self.enemy_board = not_our
        self.enemy_lives = lives

    @abstractmethod
    def choose_point(self):
        """ Куда стреляем, капитан """


class Human(Player):

    def choose_point(self):
        point = list(map(int, (input('Укажите куда будете стрелять: ').split())))
        point = list(map(lambda x: x - 1, point))
        dot = Dot(*point)
        return self.enemy_board.shoot(dot)


class Computer(Player):
    def __init__(self, our, not_our, lives):
        Player.__init__(self, our, not_our, lives)
        self.our_board.hidden = True

    def choose_point(self):
        point = Dot(randint(0, 5), randint(0, 5))
        return self.enemy_board.shoot(point)


class Game:
    def __init__(self, size):
        self.size = size

    def generate_board(self):
        while True:
            board = self.random_location()
            if board:
                return board

    def random_location(self):
        ships = [3, 2, 2, 1, 1, 1, 1]
        board = Board(self.size)
        attempt = 0
        for length in ships:
            while True:
                ship = Ship(Dot(randint(0, 5), randint(0, 5)), length, randint(0, 1))
                try:
                    board.add_ship(ship)
                except (SpotOccupied, BoardOut):
                    attempt += 1
                    if attempt == 1500:
                        return None
                else:
                    break
        return board, len(ships)

    def play_the_game(self):
        n = 1
        while True:
            print(f'\n===== Игра №{n}=====\n')
            self.play_one_game()
            choice = input('Сыграем еще раз? Для продолжения нажмите Y/y: ')
            n += 1
            if choice.lower() != 'y':
                print('Спасибо за игру!')
                break

    def play_one_game(self):
        human_board, lives = self.generate_board()
        computer_board, lives = self.generate_board()
        human = Human(human_board, computer_board, lives)
        computer = Computer(computer_board, human_board, lives)
        players = cycle([human, computer])
        player = next(players)
        while True:
            if isinstance(player, Human):
                print("Ваша доска: \n", human.our_board)
                print("Доска компьютера: \n", human.enemy_board)
            try:
                response = player.choose_point()
            except Exception as e:
                if isinstance(player, Human):
                    print(e)
                    print('Повторите ход')
                next(players)
            else:
                if isinstance(player, Human) and response:
                    print(response)
                if response == 'Ранил':
                    if isinstance(player, Human):
                        print('Повторите ход')
                    player = next(players)
                if response == 'Ранил' or response == 'Убил':
                    player.enemy_lives -= 1
                if player.enemy_lives == 0:
                    print('Победил ', player.__class__.__name__)
                    break
            player = next(players)


if __name__ == '__main__':
    g = Game(6)
    g.play_the_game()

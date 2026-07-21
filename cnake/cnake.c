/************************************************************
 * File:    cnake.c                                         *
 * Date:    2014-10-16 - 27.12.2014-12-27 (2026-07-20)      *
 * Author:  Aaron Dettmann                                  *
 * Purpose: Cnake - Primitive ASCII snake game written in C *
 ************************************************************/

#include <ctype.h>
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>

/*---------- Version ----------*/
#define VERSION "0.4.1"
#define DEFAULT_BOARD_SIZE 6
#define MIN_BOARD_SIZE 4
#define MAX_BOARD_SIZE 10

enum board_size_parse_status {
  BOARD_SIZE_INVALID = 0,
  BOARD_SIZE_OUT_OF_RANGE,
  BOARD_SIZE_VALID
};

enum game_status {
  GAME_RUNNING = 0,
  GAME_WON,
  GAME_OVER_SNAKE,
  GAME_OVER_OBSTACLE,
  GAME_OVER_POISON
};

enum command_result {
  COMMAND_ERROR = -1,
  COMMAND_QUIT = 0,
  COMMAND_SKIP_TURN,
  COMMAND_MOVE
};

/*---------- Colors ----------*/
#define RED "\x1B[31m" /* red */
#define GRN "\x1B[32m" /* green */
#define YEL "\x1B[33m" /* yellow */
#define BLU "\x1B[34m" /* blue */
#define RES "\033[0m"  /* reset */

/*---------- Escape Codes ----------*/
/*
   "\033[H"  // Move cursor to the upper-left corner of the screen
   "\033[0J" // Clear from the cursor to the end of the screen
*/

#define CLEAR "\033[H\033[0J"

/*---------- Function Prototypes ----------*/
void sig_handler(int signo);
int init_terminal(void);
void restore_terminal(void);
int read_stdin_char(char *, int);
void discard_escape_sequence(void);
int read_command(char *);
void hl(void);
void draw_border(int board_size);
void draw_game_board(int **, int, char, char, char, char, char, char,
                     const int[3], int, int);
void print_game_status_message(enum game_status, char, char, char);
void help(void);
enum board_size_parse_status parse_board_size(const char *, int *);
void free_board(int **, int);
enum command_result handle_player_command(int, char *, char *, int *, int *,
                                          int *, int *, int *);
int has_adjacent_obstacle(int **, int, int, int);
int is_spawn_position_valid(int **, int, int, int, int);
int find_spawn_position(int **, int, int, int *, int *);
enum game_status handle_tile_effect(int, int *, int[3], int *, int *);
void advance_snake(int **, int, int, int, int, int, int);
int respawn_tile_if_needed(int **, int, int, int);
int place_tile(int **, int, int);
int board_contains_value(int **, int, int);

/*---------- Terminal State ----------*/
static struct termios original_terminal;
static int terminal_initialized = 0;
static volatile sig_atomic_t interrupted = 0;

/*============================*/
/*---------- MAIN() ----------*/
/*============================*/

int main(int argc, char *argv[]) {
  /*---------- Variable Declarations ----------*/
  int i, j,               // Loop variables
      bs = 0,             // Board size --> side length of the playing field
      discard,            // Discard long board-size input
      x, y, x_old, y_old, // Position coordinates
      length = 1,      // Length of the snake
      numofobs = 0,    // Number of obstacles
      target_numofobs, // Desired number of obstacles
      stats[3] = {0, 0, 0}, // Statistics [moves][snacks eaten][poison eaten]
      show = 0,             // Show/Hide debug output
      spawn_snack = 0,      // Respawn snack after tail update
      spawn_poison = 0,     // Respawn poison after tail update
      **board = NULL;       // Game board
  char cmd = '\0',          // Command
      board_size_input[32], // Board-size prompt input
      *newline,             // Trailing newline position
      terra = ' ',          // ( 0) Empty tile
      body = '=',           // (>0) Body
      head = '>',           // (-1) Head
      obstacle = '#',       // (-2) Obstacle
      snack = '*',          // (-3) Snack
      poison = '!';         // (-4) Poison
  struct sigaction action;
  enum board_size_parse_status board_size_status;
  enum command_result command_result;
  enum game_status game_status = GAME_RUNNING;

  x = y = x_old = y_old = 0;

  /*---------- Signal Handling ----------*/
  if (atexit(restore_terminal) != 0) {
    fprintf(stderr, "Error: Unable to register terminal cleanup.\n");
    return 4;
  }

  action.sa_handler = sig_handler;
  sigemptyset(&action.sa_mask);
  action.sa_flags = 0;

  if (sigaction(SIGINT, &action, NULL) == -1) {
    fprintf(stderr, "Error: Unable to install signal handler.\n");
    return 4;
  }

  /*---------- Determine Board Size ----------*/
  hl();

  if (argc > 1 && parse_board_size(argv[1], &bs) != BOARD_SIZE_VALID)
    bs = 0;

  if (!bs) {
    do {
      printf("Choose the board size [%d-%d] (default: %d): ",
             MIN_BOARD_SIZE, MAX_BOARD_SIZE, DEFAULT_BOARD_SIZE);
      if (!fgets(board_size_input, sizeof(board_size_input), stdin))
        return 1;

      newline = strchr(board_size_input, '\n');
      if (newline == NULL)
        while ((discard = getchar()) != '\n' && discard != EOF)
          ;

      if (board_size_input[0] == '\n') {
        bs = DEFAULT_BOARD_SIZE;
        break;
      }

      board_size_status = parse_board_size(board_size_input, &bs);

      if (board_size_status == BOARD_SIZE_INVALID) {
        printf("Error: Enter a number from %d to %d, or press Enter for %d.\n",
               MIN_BOARD_SIZE, MAX_BOARD_SIZE, DEFAULT_BOARD_SIZE);
        continue;
      }

      if (board_size_status == BOARD_SIZE_OUT_OF_RANGE) {
        printf("Error: Board size must be between %d and %d.\n",
               MIN_BOARD_SIZE, MAX_BOARD_SIZE);
        continue;
      }
    } while (!bs);
  }

  if ((board = (int **)malloc(bs * sizeof(int *))) == NULL)
    return 2;

  for (i = 0; i < bs; i++)
    if ((board[i] = (int *)malloc(bs * sizeof(int))) == NULL) {
      free_board(board, i);
      return 2;
    }

  /*---------- Initialize the Board ----------*/
  for (i = 0; i < bs; i++)
    for (j = 0; j < bs; j++)
      board[i][j] = 0;

  /*---------- Seed rand() ----------*/
  srand(time(NULL));

  /*---------- Starting Position ----------*/
  board[y][x] = -1; /* head */

  /*---------- Generate Random Positions ----------*/
  target_numofobs = (int)(((bs * bs) / 10) + 1);

  for (i = 0; i < target_numofobs; i++)
    if (place_tile(board, bs, -2))
      numofobs++;
    else
      break;

  if (!place_tile(board, bs, -4) || !place_tile(board, bs, -3)) {
    fprintf(stderr, "Error: Unable to place all tiles on the board.\n");
    free_board(board, bs);
    return 3;
  }

  if (!init_terminal()) {
    fprintf(stderr, "Error: Unable to enable direct input mode.\n");
    free_board(board, bs);
    return 4;
  }

  /*---------- Start Main Game Loop ----------*/
  hl();
  printf("==> Board: %dx%d\n\n", bs, bs);

  while (1) {
    if (interrupted)
      break;

    draw_game_board(board, bs, terra, body, head, obstacle, snack, poison,
                    stats, length, show);

    if (game_status != GAME_RUNNING) {
      print_game_status_message(game_status, body, obstacle, poison);
      break;
    }

    x_old = x;
    y_old = y;

    command_result = handle_player_command(bs, &cmd, &head, &x, &y, &length,
                                           &show, &stats[0]);
    if (command_result == COMMAND_ERROR) {
      free_board(board, bs);
      return 5;
    }

    if (interrupted || command_result == COMMAND_QUIT)
      break;

    if (command_result == COMMAND_SKIP_TURN)
      continue;

    game_status = handle_tile_effect(board[y][x], &length, stats, &spawn_snack,
                                     &spawn_poison);
    if (game_status != GAME_RUNNING)
      continue;

    advance_snake(board, bs, x, y, x_old, y_old, length);

    if (!respawn_tile_if_needed(board, bs, spawn_snack, -3)) {
      fprintf(stderr, "Error: Unable to place a snack.\n");
      free_board(board, bs);
      return 3;
    }

    if (!respawn_tile_if_needed(board, bs, spawn_poison, -4)) {
      fprintf(stderr, "Error: Unable to place poison.\n");
      free_board(board, bs);
      return 3;
    }

    if (!board_contains_value(board, bs, 0)) {
      game_status = GAME_WON;
      continue;
    }

  } /* End of main game loop */

  restore_terminal();

  if (interrupted) {
    free_board(board, bs);
    printf(RES "\n\n");
    return 128 + interrupted;
  }

  /*---------- Game Summary ----------*/
  printf("\nMoves:\t\t%4d\n", stats[0]);
  printf("Snacks:\t\t%4d\n", stats[1]);
  printf("Poison:\t%4d\n", stats[2]);
  printf("Length:\t\t%d/%d+\n\n", length, (bs * bs - numofobs - 1));

  free_board(board, bs);
  return 0;

} /* End of main() */

/*================================*/
/*---------- Functions -----------*/
/*================================*/

/*---------- Signal Handling ----------*/
void sig_handler(int sigint) { interrupted = sigint; }

/*---------- Enable Direct Terminal Input ----------*/
int init_terminal(void) {
  struct termios terminal;

  if (!isatty(STDIN_FILENO))
    return 1;

  if (tcgetattr(STDIN_FILENO, &original_terminal) == -1)
    return 0;

  terminal = original_terminal;
  terminal.c_lflag &= ~(ICANON | ECHO);
  terminal.c_cc[VMIN] = 1;
  terminal.c_cc[VTIME] = 0;

  if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &terminal) == -1)
    return 0;

  terminal_initialized = 1;
  return 1;
}

/*---------- Restore Terminal Settings ----------*/
void restore_terminal(void) {
  if (!terminal_initialized)
    return;

  tcsetattr(STDIN_FILENO, TCSAFLUSH, &original_terminal);
  terminal_initialized = 0;
}

/*---------- Read One Byte from Standard Input ----------*/
int read_stdin_char(char *cmd, int timeout_ms) {
  fd_set readfds;
  struct timeval timeout;
  ssize_t bytes_read;
  int ready;

  while (1) {
    FD_ZERO(&readfds);
    FD_SET(STDIN_FILENO, &readfds);

    if (timeout_ms < 0)
      ready = select(STDIN_FILENO + 1, &readfds, NULL, NULL, NULL);
    else {
      timeout.tv_sec = timeout_ms / 1000;
      timeout.tv_usec = (timeout_ms % 1000) * 1000;
      ready = select(STDIN_FILENO + 1, &readfds, NULL, NULL, &timeout);
    }

    if (ready == 0)
      return 0;

    if (ready == -1) {
      if (errno == EINTR) {
        if (interrupted)
          return 0;

        continue;
      }

      return -1;
    }

    bytes_read = read(STDIN_FILENO, cmd, 1);

    if (bytes_read == 1)
      return 1;

    if (bytes_read == 0)
      return 0;

    if (errno == EINTR) {
      if (interrupted)
        return 0;

      continue;
    }

    return -1;
  }
}

/*---------- Discard an Unsupported Escape Sequence ----------*/
void discard_escape_sequence(void) {
  char input;
  int status;

  status = read_stdin_char(&input, 10);
  if (status != 1)
    return;

  if (input != '[' && input != 'O') {
    while (read_stdin_char(&input, 5) == 1)
      ;

    return;
  }

  do {
    status = read_stdin_char(&input, 5);
  } while (status == 1 && (input < '@' || input > '~'));
}

/*---------- Read One Command ----------*/
int read_command(char *cmd) {
  int status;

  do {
    status = read_stdin_char(cmd, -1);
    if (status != 1)
      return status;
  } while (*cmd == '\n' || *cmd == '\r');

  if (*cmd == '\033') {
    discard_escape_sequence();
    return 2;
  }

  return 1;
}

/*---------- Header ----------*/
void hl(void) { printf(CLEAR "=========== CNAKE %s ===========\n\n", VERSION); }

/*---------- Draw Outer Board Border ----------*/
void draw_border(int board_size) {
  int n;

  printf(GRN " |");

  for (n = 0; n <= 2 * board_size; n++)
    printf("-");

  printf("|\n" RES);
}

/*---------- Draw the Game Board ----------*/
void draw_game_board(int *boardl[], int bsl, char terra, char body, char head,
                     char obstacle, char snack, char poison, const int stats[3],
                     int length, int show) {
  int i, j;

  draw_border(bsl);

  for (i = 0; i < bsl; i++) {
    printf(GRN " | ");

    for (j = 0; j < bsl; j++) {
      if (boardl[i][j] > 0)
        printf(RED "%c ", body);
      else if (boardl[i][j] == 0)
        printf(RES "%c ", terra);
      else if (boardl[i][j] == -1)
        printf(RED "%c ", head);
      else if (boardl[i][j] == -2)
        printf(BLU "%c ", obstacle);
      else if (boardl[i][j] == -3)
        printf(YEL "%c ", snack);
      else if (boardl[i][j] == -4)
        printf(GRN "%c ", poison);
    }

    printf(GRN "|\t");

    if (i == 0)
      printf(RED "%c%c>\t" RES "Snake     (%d)", body, body, length);
    else if (i == 1)
      printf(YEL "%c  \t" RES "Snack     (%d)", snack, stats[1]);
    else if (i == 2)
      printf(GRN "%c  \t" RES "Poison    (%d)", poison, stats[2]);
    else if (i == 3)
      printf(BLU "%c  \t" RES "Obstacle", obstacle);

    printf(RES "\n");
  }

  draw_border(bsl);

  if (show) {
    printf("\n");

    for (i = 0; i < bsl; i++) {
      printf("|");

      for (j = 0; j < bsl; j++)
        printf("%2d ", boardl[i][j]);

      printf("|\n");
    }
  }
}

/*---------- Print the Game Status Message ----------*/
void print_game_status_message(enum game_status game_status, char body,
                               char obstacle, char poison) {
  if (game_status == GAME_WON) {
    printf("\nYOU WIN!\n");
    return;
  }

  if (game_status == GAME_OVER_SNAKE)
    printf("\nSnake!" RED " %c%c> " RES, body, body);
  else if (game_status == GAME_OVER_OBSTACLE)
    printf("\nObstacle!" BLU " %c " RES, obstacle);
  else if (game_status == GAME_OVER_POISON)
    printf("\nPoison!" GRN " %c " RES, poison);

  printf("~ GAME OVER!\n");
}

/*---------- Help ----------*/
void help(void) {
  printf("\nKeys (vim-style):\n"
         "h: move left\n"
         "j: move down\n"
         "k: move up\n"
         "l: move right\n"
         "?: show help\n"
         "c: length +5 (cheat)\n"
         "v: toggle debug view\n"
         "q: quit\n");
}

/*---------- Parse the Board Size ----------*/
enum board_size_parse_status parse_board_size(const char *input,
                                              int *board_size) {
  char *endptr;
  long parsed_bs;

  errno = 0;
  parsed_bs = strtol(input, &endptr, 10);

  if (errno != 0 || endptr == input)
    return BOARD_SIZE_INVALID;

  while (*endptr != '\0' && isspace((unsigned char)*endptr))
    endptr++;

  if (*endptr != '\0')
    return BOARD_SIZE_INVALID;

  if (parsed_bs < MIN_BOARD_SIZE || parsed_bs > MAX_BOARD_SIZE)
    return BOARD_SIZE_OUT_OF_RANGE;

  *board_size = (int)parsed_bs;
  return BOARD_SIZE_VALID;
}

/*---------- Free the Game Board ----------*/
void free_board(int **board, int rows) {
  int i;

  if (board == NULL)
    return;

  for (i = 0; i < rows; i++)
    free(board[i]);

  free(board);
}

/*---------- Read and Apply One Player Command ----------*/
enum command_result handle_player_command(int board_size, char *cmd, char *head,
                                          int *x, int *y, int *length,
                                          int *show, int *move_count) {
  int cmd_status;

  do {
    printf("\nPress a key [?]: ");
    fflush(stdout);

    cmd_status = read_command(cmd);
    if (cmd_status == -1) {
      fprintf(stderr, "\nError: Unable to read a command.\n");
      return COMMAND_ERROR;
    }

    if (cmd_status == 2)
      continue;

    if (cmd_status == 0)
      return COMMAND_QUIT;

    if (*cmd == '?') {
      help();
      continue;
    } else if (*cmd == 'k') {
      hl();
      printf("==> Up!\n\n");
      *head = '^';
      *y -= 1;
      if (*y < 0)
        *y = board_size - 1;
    } else if (*cmd == 'j') {
      hl();
      printf("==> Down!\n\n");
      *head = 'v';
      *y += 1;
      if (*y > board_size - 1)
        *y = 0;
    } else if (*cmd == 'h') {
      hl();
      printf("==> Left!\n\n");
      *head = '<';
      *x -= 1;
      if (*x < 0)
        *x = board_size - 1;
    } else if (*cmd == 'l') {
      hl();
      printf("==> Right!\n\n");
      *head = '>';
      *x += 1;
      if (*x > board_size - 1)
        *x = 0;
    } else if (*cmd == 'c') /* CHEAT CODE --> FOR TESTING */
    {
      hl();
      printf("==> Length +5!\n\n");
      *length += 5;
      return COMMAND_SKIP_TURN;
    } else if (*cmd == 'v') {
      hl();
      printf("==> Toggle Debug View!\n\n");
      *show = !*show;
      return COMMAND_SKIP_TURN;
    } else if (*cmd == 'q')
      return COMMAND_QUIT;
    else {
      printf("\nError: Unknown command!\n");
      continue;
    }

    *move_count += 1;
    return COMMAND_MOVE;

  } while (1);
}

/*---------- Check Whether an Obstacle Would Spawn Too Close ----------*/
int has_adjacent_obstacle(int *boardl[], int bsl, int x_pos, int y_pos) {
  int x_check, y_check;

  for (y_check = y_pos - 1; y_check <= y_pos + 1; y_check++)
    for (x_check = x_pos - 1; x_check <= x_pos + 1; x_check++) {
      if (y_check < 0 || y_check >= bsl || x_check < 0 || x_check >= bsl)
        continue;

      if (y_check == y_pos && x_check == x_pos)
        continue;

      if (boardl[y_check][x_check] == -2)
        return 1;
    }

  return 0;
}

/*---------- Check Whether a Spawn Position Is Valid ----------*/
int is_spawn_position_valid(int *boardl[], int bsl, int x_pos, int y_pos,
                            int type) {
  if (boardl[y_pos][x_pos] != 0)
    return 0;

  if (type == -2 && has_adjacent_obstacle(boardl, bsl, x_pos, y_pos))
    return 0;

  return 1;
}

/*---------- Find a Valid Position for a Tile ----------*/
int find_spawn_position(int *boardl[], int bsl, int type, int *x_out,
                        int *y_out) {
  int i, index, total, x_pos, y_pos, start;

  total = bsl * bsl;
  start = rand() % total;

  for (i = 0; i < total; i++) {
    index = (start + i) % total;
    y_pos = index / bsl;
    x_pos = index % bsl;

    if (is_spawn_position_valid(boardl, bsl, x_pos, y_pos, type)) {
      *x_out = x_pos;
      *y_out = y_pos;
      return 1;
    }
  }

  return 0;
}

/*---------- Apply the Current Tile Effect ----------*/
enum game_status handle_tile_effect(int tile_value, int *length, int stats[3],
                                    int *spawn_snack, int *spawn_poison) {
  *spawn_snack = 0;
  *spawn_poison = 0;

  if (tile_value > 0)
    return GAME_OVER_SNAKE;

  if (tile_value == -2)
    return GAME_OVER_OBSTACLE;

  if (tile_value == -3) {
    *length += 1;
    stats[1] += 1; /* +1 snack */
    *spawn_snack = 1;
    return GAME_RUNNING;
  }

  if (tile_value == -4) {
    stats[2] += 1; /* +1 poison */

    if (*length > 1) {
      *length -= 1;
      *spawn_poison = 1;
      return GAME_RUNNING;
    }

    return GAME_OVER_POISON;
  }

  return GAME_RUNNING;
}

/*---------- Advance the Snake ----------*/
void advance_snake(int *boardl[], int bsl, int x_pos, int y_pos,
                   int x_previous, int y_previous, int length) {
  int i, j;

  boardl[y_pos][x_pos] = -1; /* Head position */
  boardl[y_previous][x_previous] =
      length; /* Store the snake length at the previous head position */

  for (i = 0; i < bsl; i++)
    for (j = 0; j < bsl; j++)
      if (boardl[i][j] > 0) /* All values >0 are snake body segments */
        boardl[i][j] -= 1;
}

/*---------- Respawn a Consumed Tile ----------*/
int respawn_tile_if_needed(int *boardl[], int bsl, int should_respawn,
                           int type) {
  return !should_respawn || place_tile(boardl, bsl, type) ||
         !board_contains_value(boardl, bsl, 0);
}

/*---------- Place a Tile on the Board ----------*/
int place_tile(int *boardl[], int bsl, int type) {
  int x_pos, y_pos;

  if (!find_spawn_position(boardl, bsl, type, &x_pos, &y_pos))
    return 0;

  boardl[y_pos][x_pos] = type;
  return 1;
}

/*---------- Search for a Value in the Matrix ----------*/
int board_contains_value(int *boardl[], int bsl, int value) {
  int i, j;

  for (i = 0; i < bsl; i++)
    for (j = 0; j < bsl; j++)
      if (boardl[i][j] == value)
        return 1; /* Value found */

  return 0;
}

/*----- EOF -----*/

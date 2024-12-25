<?php
session_start();

$root_dir = 'site';
$users_dir = 'users';

function encrypt_password($password) {
    return password_hash($password, PASSWORD_BCRYPT);
}

function check_password($input, $hash) {
    return password_verify($input, $hash);
}

function save_user($username, $password) {
    $user_dir = $GLOBALS['users_dir'] . '/' . $username;
    if (!is_dir($user_dir)) {
        mkdir($user_dir, 0755, true);
        file_put_contents($user_dir . '/pam_' . $username . '.json', json_encode(['username' => $username, 'password' => encrypt_password($password)]));
        mkdir($GLOBALS['root_dir'] . '/' . $username, 0755, true);
        file_put_contents($GLOBALS['root_dir'] . '/' . $username . '/index.html', '<h1>Welcome to your site, ' . $username . '!</h1>');
    }
}

function check_user($username, $password) {
    $user_dir = $GLOBALS['users_dir'] . '/' . $username;
    if (is_dir($user_dir)) {
        $user_data = json_decode(file_get_contents($user_dir . '/pam_' . $username . '.json'), true);
        return check_password($password, $user_data['password']);
    }
    return false;
}

function user_exists($username) {
    $user_dir = $GLOBALS['users_dir'] . '/' . $username;
    return is_dir($user_dir);
}

function is_authenticated() {
    return isset($_SESSION['authenticated']) && $_SESSION['authenticated'];
}

function authenticate($username) {
    $_SESSION['authenticated'] = true;
    $_SESSION['username'] = $username;
}

function logout() {
    session_unset();
    session_destroy();
}

function delay() {
    sleep(1);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    delay();
    if (isset($_POST['action'])) {
        $action = $_POST['action'];
        if ($action === 'register') {
            $username = $_POST['username'];
            $password = $_POST['password'];
            if (!user_exists($username)) {
                save_user($username, $password);
                authenticate($username);
                header('Location: ' . $_SERVER['PHP_SELF']);
                exit;
            } else {
                echo '<p>User already exists. <a href="?">Try again</a></p>';
                exit;
            }
        } elseif ($action === 'login') {
            $username = $_POST['username'];
            $password = $_POST['password'];
            if (check_user($username, $password)) {
                authenticate($username);
                header('Location: ' . $_SERVER['PHP_SELF']);
                exit;
            } else {
                echo '<p>Incorrect username or password. <a href="?">Try again</a></p>';
                exit;
            }
        } elseif ($action === 'logout') {
            logout();
            header('Location: ' . $_SERVER['PHP_SELF']);
            exit;
        }
    }
}

if (!is_authenticated()) {
    if (isset($_GET['action']) && $_GET['action'] === 'register') {
        echo '<form method="post">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password">
                <button type="submit" name="action" value="register">Register</button>
              </form>';
        exit;
    } else {
        echo '<form method="post">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password">
                <button type="submit" name="action" value="login">Login</button>
                <a href="?action=register">Register</a>
              </form>';
        exit;
    }
}

$current_user = $_SESSION['username'];
$current_dir = isset($_GET['dir']) ? $_GET['dir'] : $root_dir . '/' . $current_user;
$files = scandir($current_dir);

function is_dir_path($path) {
    return is_dir($path) && !in_array(basename($path), ['.', '..']);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && is_authenticated()) {
    if (isset($_POST['action'])) {
        $action = $_POST['action'];
        $path = $_POST['path'];

        switch ($action) {
            case 'rename':
                $newName = $_POST['newName'];
                $newPath = dirname($path) . '/' . $newName;
                if (is_dir($path)) {
                    rename($path, $newPath);
                } else {
                    rename($path, $newPath);
                }
                break;
            case 'delete':
                if (is_dir($path)) {
                    rmdir($path);
                } else {
                    unlink($path);
                }
                break;
            case 'clone':
                $newPath = $path . '_copy';
                if (is_dir($path)) {
                    mkdir($newPath);
                    $files = scandir($path);
                    foreach ($files as $file) {
                        if ($file === '.' || $file === '..') continue;
                        copy($path . '/' . $file, $newPath . '/' . $file);
                    }
                } else {
                    copy($path, $newPath);
                }
                break;
            case 'create':
                $newFile = $current_dir . '/' . $_POST['newFile'];
                file_put_contents($newFile, '');
                break;
            case 'save':
                $content = $_POST['content'];
                file_put_contents($path, $content);
                break;
            case 'create_dir':
                $newDir = $current_dir . '/' . $_POST['newDir'];
                mkdir($newDir);
                break;
        }
        header('Location: ' . $_SERVER['PHP_SELF'] . '?dir=' . urlencode($current_dir));
        exit;
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Manager</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="header">
        <h1>File Manager</h1>
        <button id="home">Home</button>
        <button id="back">Back</button>
        <button id="logout">Logout</button>
    </div>
    <div class="file-list">
        <?php foreach ($files as $file): ?>
            <?php if ($file === '.' || $file === '..') continue; ?>
            <div class="file-item">
                <input type="checkbox" class="file-checkbox" data-path="<?= $current_dir . '/' . $file ?>">
                <?php if (is_dir_path($current_dir . '/' . $file)): ?>
                    <a href="?dir=<?= $current_dir . '/' . $file ?>">
                        <img src="https://cdn.icon-icons.com/icons2/1129/PNG/512/folderblacksymbol_79730.png" alt="Folder" class="icon">
                        <?= $file ?>
                    </a>
                <?php else: ?>
                    <a href="?file=<?= $current_dir . '/' . $file ?>">
                        <img src="https://cdn.icon-icons.com/icons2/1129/PNG/512/fileinterfacesymboloftextpapersheet_79740.png" alt="File" class="icon">
                        <?= $file ?>
                    </a>
                    <a href="<?= $current_dir . '/' . $file ?>" target="_blank" class="open-web-btn">Open Web</a>
                <?php endif; ?>
            </div>
        <?php endforeach; ?>
    </div>

    <?php if (isset($_GET['file'])): ?>
        <div class="file-editor">
            <h2>Edit File: <?= basename($_GET['file']) ?></h2>
            <form action="" method="post">
                <textarea name="content" rows="10" cols="50"><?php echo htmlspecialchars(file_get_contents($_GET['file'])); ?></textarea>
                <input type="hidden" name="path" value="<?= $_GET['file'] ?>">
                <input type="hidden" name="action" value="save">
                <button type="submit">Save</button>
            </form>
        </div>
    <?php endif; ?>

    <div class="actions">
        <button id="create">Create File</button>
        <button id="create_dir">Create Directory</button>
        <button id="rename">Rename</button>
        <button id="delete">Delete</button>
        <button id="clone">Clone</button>
    </div>

    <script>
        document.getElementById('home').addEventListener('click', function() {
            window.location.href = '?dir=<?= $root_dir . '/' . $current_user ?>';
        });

        document.getElementById('back').addEventListener('click', function() {
            const currentDir = '<?= $current_dir ?>';
            const parentDir = currentDir.split('/').slice(0, -1).join('/');
            window.location.href = '?dir=' + encodeURIComponent(parentDir);
        });

        document.getElementById('logout').addEventListener('click', function() {
            const form = document.createElement('form');
            form.method = 'post';
            form.innerHTML = `
                <input type="hidden" name="action" value="logout">
            `;
            document.body.appendChild(form);
            form.submit();
        });

        document.getElementById('create').addEventListener('click', function() {
            const newFileName = prompt('Enter new file name:');
            if (newFileName) {
                const form = document.createElement('form');
                form.method = 'post';
                form.innerHTML = `
                    <input type="hidden" name="action" value="create">
                    <input type="hidden" name="newFile" value="${newFileName}">
                `;
                document.body.appendChild(form);
                form.submit();
            }
        });

        document.getElementById('create_dir').addEventListener('click', function() {
            const newDirName = prompt('Enter new directory name:');
            if (newDirName) {
                const form = document.createElement('form');
                form.method = 'post';
                form.innerHTML = `
                    <input type="hidden" name="action" value="create_dir">
                    <input type="hidden" name="newDir" value="${newDirName}">
                `;
                document.body.appendChild(form);
                form.submit();
            }
        });

        document.getElementById('rename').addEventListener('click', function() {
            const selectedFiles = getSelectedFiles();
            if (selectedFiles.length === 1) {
                const newName = prompt('Enter new name:');
                if (newName) {
                    const form = document.createElement('form');
                    form.method = 'post';
                    form.innerHTML = `
                        <input type="hidden" name="action" value="rename">
                        <input type="hidden" name="path" value="${selectedFiles[0]}">
                        <input type="hidden" name="newName" value="${newName}">
                    `;
                    document.body.appendChild(form);
                    form.submit();
                }
            } else {
                alert('Please select one file to rename.');
            }
        });

        document.getElementById('delete').addEventListener('click', function() {
            const selectedFiles = getSelectedFiles();
            if (selectedFiles.length > 0) {
                if (confirm('Are you sure you want to delete selected files?')) {
                    const form = document.createElement('form');
                    form.method = 'post';
                    selectedFiles.forEach(file => {
                        form.innerHTML += `
                            <input type="hidden" name="action" value="delete">
                            <input type="hidden" name="path" value="${file}">
                        `;
                    });
                    document.body.appendChild(form);
                    form.submit();
                }
            } else {
                alert('Please select files to delete.');
            }
        });

        document.getElementById('clone').addEventListener('click', function() {
            const selectedFiles = getSelectedFiles();
            if (selectedFiles.length > 0) {
                const form = document.createElement('form');
                form.method = 'post';
                selectedFiles.forEach(file => {
                    form.innerHTML += `
                        <input type="hidden" name="action" value="clone">
                        <input type="hidden" name="path" value="${file}">
                    `;
                });
                document.body.appendChild(form);
                form.submit();
            } else {
                alert('Please select files to clone.');
            }
        });

        function getSelectedFiles() {
            const checkboxes = document.querySelectorAll('.file-checkbox:checked');
            return Array.from(checkboxes).map(checkbox => checkbox.dataset.path);
        }
    </script>
</body>
</html>
